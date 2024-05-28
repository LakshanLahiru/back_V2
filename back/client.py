from binance.client import Client

class api_secret_client:
    api_key = "b6ba865a8a866e27a29769183953ae47762ea98861118d3e67c0ea0f52f04488"
    secret_key = "af692e426d8f9a27a83c7daeea25a81da4270e22bb8337eb7e858488738babd3"
    client = Client(api_key = api_key, api_secret = secret_key, tld = "com", testnet = True)
    symbol ="BTCUSDT"