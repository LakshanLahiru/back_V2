from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from flask import request
from client import api_secret_client

app = Flask(__name__)
CORS(app)

api_key = api_secret_client.api_key
secret_key =api_secret_client.secret_key
client = api_secret_client.client
symbol= api_secret_client.symbol

# Taking database details
def connect_db():
    return mysql.connector.connect(host="localhost", user="root", password="ABCDEf45@", database="binance")



def execute_query(query, params=None):
    try:
        db = connect_db()
        cursor = db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        data = cursor.fetchall()
        return data
    except Exception as e:
        return {'error': str(e)}
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()


@app.route('/api/data', methods=['GET'])
def get_data():
    query = "SELECT * FROM back ORDER BY closeTime DESC"
    data = execute_query(query)
    
    return jsonify(data)

@app.route('/api/profit', methods=['GET'])
def get_profit_data():
 
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')


    query = "SELECT SUM(profit) AS total_profit FROM back WHERE STR_TO_DATE(openTime, '%Y-%m-%d %H:%i:%s') BETWEEN '" + start_date + " 00:00:00' AND '" + end_date + " 00:00:00'"


    data = execute_query(query)
    
    return jsonify(data)

if __name__ == '__main__':
      app.run(debug=True, port=5000)
