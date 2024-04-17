import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd
from flask import jsonify

load_dotenv()

db_hostname = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_database = os.getenv('DB_DATABASE')

def db_connect():
    try:
        conn =  psycopg2.connect(
            host=db_hostname,
            port=db_port,
            user=db_username,
            password=db_password,
            database=db_database
        )

        return conn
    except psycopg2.Error as e:
        return jsonify({'error_db_connection': str(e)})
    

def load_sales_data():
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales_data")
        sales_data = cursor.fetchall()
        # Convert the sales data to a pandas DataFrame
        df = pd.DataFrame(sales_data, columns=['day', 'total_sales'])

        cursor.execute("SELECT date FROM sales_data ORDER BY date DESC LIMIT 1;")
        last_day = cursor.fetchall()
        last_day = last_day[0][0].strftime('%Y-%m-%d')
        # conn.close()
        return conn, df, last_day.split()[0]
    except psycopg2.Error as e:
        return jsonify({'error_db_connection': str(e)})