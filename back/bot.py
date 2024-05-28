from datetime import datetime, timedelta
from binance.client import Client
import pandas as pd
import requests
import json
import logging
import pandas_ta as ta
import numpy as np
import scipy.optimize as opt
import mplfinance as mpf
from stocktrends import Renko
import matplotlib.pyplot as plt
import mysql.connector
import time
import schedule
import logging


Format = '%(asctime)s-%(message)s'
logging.basicConfig(level=logging.INFO, format=Format)

class HistoricalData:
    @staticmethod
    def update_daily():
        now = datetime.now()
        start_date = now - timedelta(days=100)  # Start date is 100 days ago from now
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(now.timestamp() * 1000)  # End timestamp is current time
        symbol = 'BTCUSDT'
        interval = '4h'

        df = HistoricalData.getting_Binance_data(symbol, interval, start_timestamp, end_timestamp)
        return df

    @staticmethod
    def getting_Binance_data(symbol, interval, start, end):
        endpoint = 'https://api.binance.com/api/v3/klines'
        limit = 1000
        request_params = {'symbol': symbol, 'interval': interval, 'startTime': start, 'endTime': end, 'limit': limit}
        response = requests.get(endpoint, params=request_params)
        data = json.loads(response.text)
        df = pd.DataFrame(data)
        df = df.iloc[:, 0:6]
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df["Date"] = pd.to_datetime(df["Date"], unit='ms')
        df["Close"] = pd.to_numeric(df["Close"], errors='coerce')
        df["High"] = pd.to_numeric(df["High"], errors='coerce')
        df["Low"] = pd.to_numeric(df["Low"], errors='coerce')
      
        df.set_index("Date", inplace=True)# Convert date to datetime format
        renko_df = HistoricalData.renko_data(df)
        
        return df
    def renko_data(data):  # Get the Renko data
        # For a stable backtest we need to drop tha last row of the dataframe
        # This is because you want to backtest with any live candles
        # In this case the CCXT's last data points (last row) is live so that's why we need to drop it
        # In other words you want completed candles
        #data.drop(data.index[-1], inplace=True)

        data['ATR'] = ta.atr(high=data['High'], low=data['Low'], close=data['Close'], length=14)
        
        data.dropna(inplace=True)
       

        def evaluate_brick_size_atr(brick_size, atr_values):
            # Calculate number of bricks based on ATR and brick size
            num_bricks = atr_values // brick_size
            return np.sum(num_bricks)

        # Get optimised brick size
        brick = opt.fminbound(lambda x: -evaluate_brick_size_atr(x, data['ATR']), np.min(
            data['ATR']), np.max(data['ATR']), disp=0)

        def custom_round(number):
            # List of available rounding values
            rounding_values = [0.001, 0.005, 0.01, 0.05,
                               0.1, 0.5, 1] + list(range(5, 100, 5))
            rounding_values += list(range(100, 1000, 50)) + \
                list(range(1000, 10000, 100))

            # Finding the closest rounding value
            closest_value = min(rounding_values, key=lambda x: abs(x - number))
            return closest_value
        brick_size =custom_round(brick)
        #print(f'brick size: {brick_size}')
        data.reset_index(inplace=True)
        data.columns = [i.lower() for i in data.columns]
        
        df = Renko(data)
       
        df.brick_size = brick_size
        renko_df = df.get_ohlc_data()
        
        # Capitalize the Column names for ohlc
        renko_df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

        # Return the ohlc colums to floats
        renko_df['Open'] = renko_df['Open'].astype(float)
        renko_df['High'] = renko_df['High'].astype(float)
        renko_df['Low'] = renko_df['Low'].astype(float)
        renko_df['Close'] = renko_df['Close'].astype(float)
        
        positions_df = HistoricalData.generate_positions(renko_df)
        
        return renko_df
    
    def generate_positions(renko_df):
        # Rename the index of the renko data to brick
        renko_df.index.name = "brick"

        # Initialize signals list with 0 (no signal) for the first brick
        signals = []
        desition  = 0
        

        for i in range(0, len(renko_df)):
            # Get the current and previous brick colors
            is_current_green = renko_df['Close'].iloc[i] > renko_df['Open'].iloc[i]
            is_prev_green = renko_df['Close'].iloc[i -1] > renko_df['Open'].iloc[i - 1]

            if is_current_green and not is_prev_green:
                signals.append(1)  # Buy signal when the brick changes to green # prev red current green buy
            elif is_current_green and is_prev_green:
                signals.append(1)  # Hold signal when the brick remains green # prev green and current green hold 
            elif not is_current_green and is_prev_green:
                signals.append(-1)  # Sell signal when the brick changes to red # prev green and current red 
            elif not is_current_green and not is_prev_green:
                signals.append(-1)  # Hold signal when the brick remains red # prev red and current red

         # Add the 'signals' column to the DataFrame
        renko_df['signals'] = signals
        renko_df['signals'] = renko_df["signals"].shift(1) #Remove look ahead bias
        renko_df.fillna(0.0, inplace=True)
        renko_df.set_index("Date", inplace=True)

        # Create the Positions
        # Initialize positions with nan
        renko_df['buy_positions'] = np.nan
        renko_df['sell_positions'] = np.nan

        renko_df.index.freq = pd.infer_freq(renko_df.index)

       # Update the buy_positions with the close price where the signal is 1 and the previous signal is not equal to the current signal
        buy_signal_indices = renko_df[(renko_df['signals'] == 1) & (renko_df['signals'] != renko_df['signals'].shift(1))].index
        renko_df.loc[buy_signal_indices, 'buy_positions'] = renko_df.loc[buy_signal_indices, 'Close']

        # Update the sell_positions with close price where the signal is -1 and the previous signal is not equal to the current signal
        sell_signal_indices = renko_df[(renko_df['signals'] == -1) & (renko_df['signals'] != renko_df['signals'].shift(1))].index
        renko_df.loc[sell_signal_indices, 'sell_positions'] = renko_df.loc[sell_signal_indices, 'Close']

        # Reset duplicate dates in the positions to nan, i.e where the previous date is equal to the current date
        renko_df.loc[renko_df.index == pd.Series(renko_df.index).shift(1), ['buy_positions', 'sell_positions']] = np.nan
        #print(renko_df)
        
        #print(renko_df['sell_positions'].notnull().sum())
        #print(renko_df['buy_positions'].notnull().sum())
        
        
        if renko_df['signals'].iloc[-1] ==1:
            desition = 1
        if renko_df['signals'].iloc[-1] ==-1:
            desition = -1
        
        
        
#real one
#         if renko_df['sell_positions'].iloc[-1] >0 :
#             desition = -1
#             print(renko_df['sell_positions'].iloc[-1])
#         if renko_df['buy_positions'].iloc[-1] >0 :
#             desition = 1
#             print(renko_df['buy_positions'].iloc[-1])
#         else:
#              desition = 0
#         HistoricalData.calculate_strategy_performance(renko_df)
#         HistoricalData.plot_renko(renko_df)
        instance_x = shedule_Orders()
        instance_x.calling_for_trade(desition)
        
        return renko_df
    
class API:
    api_key = "b6ba865a8a866e27a29769183953ae47762ea98861118d3e67c0ea0f52f04488"
    secret_key = "af692e426d8f9a27a83c7daeea25a81da4270e22bb8337eb7e858488738babd3"
    client = Client(api_key = api_key, api_secret = secret_key, tld = "com", testnet = True)
class shedule_Orders:
    usdt_balance_before =0
    usdt_balance_after = 0
    ROI =0
    delta=0
    entry_price=0
    close_price = 0
    marketPrice =0
    orderId =0
    unRealizedProfit=0
    profit =0
    size=0
    symbol ="BTCUSDT"
    leverage = 10
    coin = None
    closeTime = None
    openTime = None
    side =''
    desition = 0
    
    def calling_for_trade(self,desition):
        logging.info(f'desition = {desition}')
        if (desition ==1):
            
            shedule_Orders.side="BUY"
            shedule_Orders.openTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            shedule_Orders.get_btcusdt_price()
            shedule_Orders.entry_price=shedule_Orders.marketPrice
            shedule_Orders.desition = 1
            logging.info(f'Open Time = {shedule_Orders.openTime}')
            logging.info(f'Entry Price ={shedule_Orders.marketPrice}')
            #data_base_conector.insert_data(shedule_Orders.openTime , shedule_Orders.marketPrice, shedule_Orders.desition,shedule_Orders.side)
            shedule_Orders.sl_tp(desition);
            # time.sleep(14400)
            
                      
            # shedule_Orders.close_order(desition)

            
        if (desition ==-1):
            shedule_Orders.side="SELL"
            shedule_Orders.openTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            shedule_Orders.get_btcusdt_price()
            shedule_Orders.entry_price=shedule_Orders.marketPrice
            shedule_Orders.desition = -1
            logging.info(f'Open Time = {shedule_Orders.openTime}')
            logging.info(f'Entry Price ={shedule_Orders.marketPrice}') 
            
            #data_base_conector.insert_data(shedule_Orders.openTime , shedule_Orders.marketPrice, shedule_Orders.desition,shedule_Orders.side)
            shedule_Orders.sl_tp(desition);
            # time.sleep(14400)
            
            # shedule_Orders.close_order(desition)

    def sl_tp(desition):
        if (desition==1):
            sl=0.995*shedule_Orders.entry_price
            tp =1.015*shedule_Orders.entry_price
            isTrue = True
            time1 = datetime.strptime(shedule_Orders.openTime, '%Y-%m-%d %H:%M:%S')
            while(isTrue):
                
                time2_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current time in YYYY-MM-DD HH:MM:SS format
                time2 = datetime.strptime(time2_str, '%Y-%m-%d %H:%M:%S') 
                shedule_Orders.delta=(time2-time1).total_seconds()
                shedule_Orders.get_btcusdt_price()
                if(shedule_Orders.marketPrice>=tp or shedule_Orders.marketPrice<=sl or shedule_Orders.delta >=14400 ) :
                    #Time 
                    shedule_Orders.close_order(desition)
                    break
                time.sleep(60)

        if(desition==-1):
            sl=1.005*shedule_Orders.entry_price
            tp = 0.985*shedule_Orders.entry_price
            time1 = datetime.strptime(shedule_Orders.openTime, '%Y-%m-%d %H:%M:%S')
            isTrue = True
            while(isTrue):
                time2_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current time in YYYY-MM-DD HH:MM:SS format
                time2 = datetime.strptime(time2_str, '%Y-%m-%d %H:%M:%S') 
                shedule_Orders.delta=(time2-time1).total_seconds()
                shedule_Orders.get_btcusdt_price()

                if (shedule_Orders.marketPrice<=tp or shedule_Orders.marketPrice>=sl or shedule_Orders.delta >=14400):
                    shedule_Orders.close_order(desition)
                    break
                time.sleep(60)
                    
                    




        
        
    def close_order(desition):
            shedule_Orders.get_btcusdt_price()
            shedule_Orders.close_price = shedule_Orders.marketPrice
            shedule_Orders.closeTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f'close Time = {shedule_Orders.closeTime}')
            logging.info(f'close Price ={shedule_Orders.marketPrice}') 

            #assume capital will be 1000USDT and laverage  = 10
            
            shedule_Orders.profit  = round(((float(shedule_Orders.close_price) - float(shedule_Orders.entry_price))/float(shedule_Orders.entry_price))*(desition)*10*1000,2)
            #shedule_Orders.ROI = round((float(shedule_Orders.close_price) - float(shedule_Orders.entry_price))/float(shedule_Orders.entry_price)*100,2)
            shedule_Orders.ROI = round((shedule_Orders.profit/100),2)
            logging.info(f'Profit = {shedule_Orders.profit}')
            logging.info(f'ROI = { shedule_Orders.ROI}')
            data_base_conector.insert_data(shedule_Orders.openTime,shedule_Orders.closeTime,
                                           shedule_Orders.entry_price,shedule_Orders.close_price,desition,shedule_Orders.side,shedule_Orders.profit
                                          ,shedule_Orders.ROI)
            time.sleep(1)
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            HistoricalData.update_daily()
            
            
    def get_btcusdt_price():
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
        headers = {'X-MBX-APIKEY': API.api_key}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            shedule_Orders.marketPrice = float(data['price'])
            
            return shedule_Orders.marketPrice
        else:
            logging.info('Failed to fetch BTCUSDT price.')
            return None
        
class data_base_conector:
    
    def insert_data(openTime,closeTime,entryPrice,closePrice ,decision,side,profit,ROI):
        try:  
            mydb = mysql.connector.connect(host="localhost", user="root", password="ABCDEf45@",database="binance")
            mycursor = mydb.cursor()
            sql = "INSERT INTO back_v2 (openTime,closeTime,entryPrice,closePrice ,decision,side,profit,ROI ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (openTime,closeTime,entryPrice,closePrice ,decision,side,profit,ROI)
            mycursor.execute(sql, val)
            mydb.commit()
        except mysql.connector.Error as err:
            logging.error(f'Error inserting data: {err}')
        finally:
            if mydb.is_connected():
                mydb.close()
        
        
    
    
        
        
            

        
    
ob1 = HistoricalData()
#df=ob1.update_daily()



schedule.every().day.at("00:01:00").do(ob1.update_daily)


while True:
    schedule.run_pending()
    time.sleep(1)
