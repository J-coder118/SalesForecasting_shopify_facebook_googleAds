from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from app.db import database as db
import requests
from dotenv import load_dotenv
import os
from app.db.sales import Sales
from app.db.ads import Ads
from app.prediction import sales_predict as sp
import time

load_dotenv()


def fetch_daily_shopify_data(user):
    shopify_data =  fetch_shopify_data(user)
    # Update your database or perform any other necessary actions with the fetched data
    conn = db.db_connect()
    cursor = conn.cursor()
    # Check for duplicate dates before inserting
    for entry in shopify_data:
        date_to_check = entry["date"]
        cursor.execute("SELECT * FROM sales WHERE date = %s AND userid = %s", (date_to_check,user.id))
        existing_data = cursor.fetchone()

        if existing_data:
            print(f"Data for {date_to_check} already exists. Skipping insertion.")
        else:
            # Insert new data
            cursor.execute("INSERT INTO sales (date, total_sales, orders, userid) VALUES (%s, %s, %s)",
                           (date_to_check, entry["total_sales"], entry["orders"], user.id))
            print(f"Data for {date_to_check} inserted successfully.")
    conn.commit()
    print("Shopify data fetched and updated")
    ## model generate

    

def fetch_shopify_data(user):
    sh_domain = user.sh_domain
    access_token = user.sh_token

    url = f"https://{sh_domain}/admin/api/2023-10/graphql.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }
    yesterday = datetime.now() - timedelta(days=2)
    formatted_date = yesterday.strftime('%Y-%m-%dT%H:%M:%S%z')
    today = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
    print("============")
    graphql_query = '''
    query {
        shop {
            name
        }
        orders(first: 100, query: "created_at:>'%s' AND created_at:<'%s'") {
            pageInfo {
                hasNextPage
                endCursor
            }
            edges {
                node {
                    id
                    createdAt
                    totalPriceSet {
                        shopMoney {
                            amount
                        }
                    }
                }
            }
        }
    }
    ''' % (formatted_date, today)

    all_orders = []
    try:
        response = requests.post(url, json={'query': graphql_query}, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        orders = data.get('data', {}).get('orders', {}).get('edges', [])
        all_orders.extend(orders)
        # time.sleep(5)  # Add a delay to avoid rate limiting
    except Exception as e:
        print(f"Error fetching orders: {e}")
    return calculate_daily_total_sales(all_orders)


def calculate_daily_total_sales(orders_data):
    daily_total_sales = {}

    for order in orders_data:
        order_date_str = order['node']['createdAt']
        order_date = datetime.strptime(order_date_str, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=7)
        
        # Assuming you want to compare with the date only
        target_date_start = order_date.replace(hour=0, minute=0, second=0, microsecond=0)
        target_date_str = target_date_start.strftime("%m-%d-%Y")
        
        total_sales = float(order['node']['totalPriceSet']['shopMoney']['amount'])

        # Check if the date already exists in daily_total_sales
        if target_date_str in daily_total_sales:
            # Update total_sales for the specific date
            daily_total_sales[target_date_str]['total_sales'] += total_sales
            daily_total_sales[target_date_str]['total_orders'] += 1
        else:
            # Add the date to daily_total_sales
             daily_total_sales[target_date_str] = {'total_sales': total_sales, 'total_orders': 1}
                        
    # Convert the dictionary back to a list of dictionaries
    result = [{"date": date, "total_sales": sales_data['total_sales'], "orders": sales_data["total_orders"]} for date, sales_data in daily_total_sales.items()]
    print("shopify-result", result)
    return result


def fetch_all_shopify_data(user):
    sh_domain = user.sh_domain
    access_token = user.sh_token
    url = f"https://{sh_domain}/admin/api/2023-10/graphql.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }
    yesterday = datetime.now() - timedelta(days=2)
    formatted_date = yesterday.strftime('%Y-%m-%dT%H:%M:%S%z')
    today = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
    print("============")
    end_cursor = []
    has_next_page = True
    graphql_query = '''
        query {
            shop {
                name
            }
            orders(first: 250) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                edges {
                    node {
                        id
                        createdAt
                        totalPriceSet {
                            shopMoney {
                                amount
                            }
                        }
                    }
                }
            }
        }
        ''' 
    while has_next_page: 
        if end_cursor:
            graphql_query = '''
                query {
                    shop {
                        name
                    }
                    orders(first: 250, after: "%s") {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                id
                                createdAt
                                totalPriceSet {
                                    shopMoney {
                                        amount
                                    }
                                }
                            }
                        }
                    }
                }
                ''' % (end_cursor)
        else:
            graphql_query = '''
                query {
                    shop {
                        name
                    }
                    orders(first: 250) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                id
                                createdAt
                                totalPriceSet {
                                    shopMoney {
                                        amount
                                    }
                                }
                            }
                        }
                    }
                }
                '''
        all_orders = []
        try:
            response = requests.post(url, json={'query': graphql_query}, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()
            orders = data.get('data', {}).get('orders', {}).get('edges', [])
            print(orders)
            all_orders.extend(orders)
            all_shopify_data = calculate_daily_total_sales(all_orders)

            conn = db.db_connect()
            cursor = conn.cursor()
            # Check for duplicate dates before inserting
            for entry in all_shopify_data:
                date_to_check = entry["date"]
                cursor.execute("SELECT * FROM sales WHERE date = %s", (date_to_check,))
                existing_data = cursor.fetchone()

                if existing_data:
                    print(f"Data for {date_to_check} already exists. Skipping insertion.")
                else:
                    # Insert new data
                    cursor.execute("INSERT INTO sales (date, total_sales, orders, userid) VALUES (%s, %s, %s, %s)",
                                (date_to_check, entry["total_sales"], entry["orders"], user.id))
                    print(f"Data for {date_to_check} inserted successfully.")
            conn.commit()
            print("Shopify data inserted")
            
            
            has_next_page = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('hasNextPage', False)
            end_cursor = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('endCursor', None)
            time.sleep(5)  # Add a delay to avoid rate limiting
        except Exception as e:
            print(f"Error fetching orders: {e}")

    return "success"
    # return all_orders


## product data.
def fetch_product_data(user):
    sh_domain = user.sh_domain
    access_token = user.sh_token
    url = f"https://{sh_domain}/admin/api/2023-10/graphql.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }
    yesterday = datetime.now() - timedelta(days=2)
    formatted_date = yesterday.strftime('%Y-%m-%dT%H:%M:%S%z')
    today = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
    end_cursor = []
    has_next_page = True
    product_data = {}  # Dictionary to store product data

    graphql_query = '''
        query {
            shop {
                name
            }
            orders(first: 250) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                edges {
                    node {
                        id
                        createdAt
                        totalPriceSet {
                            shopMoney {
                                amount
                            }
                        }
                        lineItems(first: 5) {
                            edges {
                                node {
                                    title
                                    quantity
                                    originalTotalSet {
                                        shopMoney {
                                            amount
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        ''' 
    while has_next_page: 
        if end_cursor:
            graphql_query = '''
                query {
                    shop {
                        name
                    }
                    orders(first: 250, after: "%s") {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                id
                                createdAt
                                totalPriceSet {
                                    shopMoney {
                                        amount
                                    }
                                }
                                lineItems(first: 5) {
                                    edges {
                                        node {
                                            title
                                            quantity
                                            originalTotalSet {
                                                shopMoney {
                                                    amount
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                ''' % (end_cursor)
        else:
            graphql_query = '''
                query {
                    shop {
                        name
                    }
                    orders(first: 250) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                id
                                createdAt
                                totalPriceSet {
                                    shopMoney {
                                        amount
                                    }
                                }
                                lineItems(first: 5) {
                                    edges {
                                        node {
                                            title
                                            quantity
                                            originalTotalSet {
                                                shopMoney {
                                                    amount
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                '''
        try:
            response = requests.post(url, json={'query': graphql_query}, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()
            orders = data.get('data', {}).get('orders', {}).get('edges', [])
            
            for order in orders:
                line_items = order['node']['lineItems']['edges']
                for line_item in line_items:
                    product_name = line_item['node']['title']
                    quantity = line_item['node']['quantity']
                    price = line_item['node']['originalTotalSet']['shopMoney']['amount']
                    total_price = float(price) * quantity

                    # Check if product already exists in product_data dictionary
                    if product_name in product_data:
                        # Update the existing product's price and order count
                        product_data[product_name]['total_price'] += total_price
                        product_data[product_name]['order_count'] += 1
                    else:
                        # Add a new product to the product_data dictionary
                        product_data[product_name] = {
                            'total_price': total_price,
                            'order_count': 1
                        }
            print(product_data)
            has_next_page = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('hasNextPage', False)
            end_cursor = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('endCursor', None)
            time.sleep(5)  # Add a delay to avoid rate limiting
            result = insert_product(user.id, product_data)
            return result
        except Exception as e:
            print(f"Error fetching orders: {e}")


def insert_product(user_id, product_data):
            for key, value in product_data.items():
                order_count = value["order_count"]
                total_price = value["total_price"]
                print(f"Key: {key}, Order Count: {order_count}, Total Price: {total_price}")

                conn = db.db_connect()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE name = %s AND userid = %s", (key, user_id))
                existing_data = cursor.fetchone()

                if existing_data:
                    return "User already registered the products data."
                else:
                    cursor.execute("INSERT INTO products (name, tcost, torder, userid) VALUES (%s, %s, %s, %s)",
                           (key, total_price, order_count, user_id))
            return "Products data inserted successfully."
                    
    
    ## daily update
def fetch_daily_product_data(user):
        sh_domain = user.sh_domain
        access_token = user.sh_token
 
        url = f"https://{sh_domain}/admin/api/2023-10/graphql.json"

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }
        yesterday = datetime.now() - timedelta(days=2)
        formatted_date = yesterday.strftime('%Y-%m-%d')
        start_time = yesterday.strftime('%Y-%m-%dT00:00:00%z')
        end_time = yesterday.strftime('%Y-%m-%dT23:59:59%z')
        end_cursor = []
        has_next_page = True
        product_data = {}  # Dictionary to store product data

        graphql_query = '''
            query {
                shop {
                    name
                }
                orders(first: 250, query: "created_at:>'%s' AND created_at:<'%s'") {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            id
                            createdAt
                            totalPriceSet {
                                shopMoney {
                                    amount
                                }
                            }
                            lineItems(first: 250) {
                                edges {
                                    node {
                                        title
                                        quantity
                                        originalTotalSet {
                                            shopMoney {
                                                amount
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            '''  % (start_time, end_time)
        while has_next_page: 
            if end_cursor:
                graphql_query = '''
                    query {
                        shop {
                            name
                        }
                        orders(first: 250, after: "%s") {
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                            edges {
                                node {
                                    id
                                    createdAt
                                    totalPriceSet {
                                        shopMoney {
                                            amount
                                        }
                                    }
                                    lineItems(first: 250) {
                                        edges {
                                            node {
                                                title
                                                quantity
                                                originalTotalSet {
                                                    shopMoney {
                                                        amount
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    ''' % (end_cursor)
            else:
                graphql_query = '''
                    query {
                        shop {
                            name
                        }
                        orders(first: 250, query: "created_at:>'%s' AND created_at:<'%s'") {
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                            edges {
                                node {
                                    id
                                    createdAt
                                    totalPriceSet {
                                        shopMoney {
                                            amount
                                        }
                                    }
                                    lineItems(first: 250) {
                                        edges {
                                            node {
                                                title
                                                quantity
                                                originalTotalSet {
                                                    shopMoney {
                                                        amount
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    ''' % (start_time, end_time)
            try:
                response = requests.post(url, json={'query': graphql_query}, headers=headers)
                response.raise_for_status()  # Check for HTTP errors
                data = response.json()
                orders = data.get('data', {}).get('orders', {}).get('edges', [])
                for order in orders:
                    line_items = order['node']['lineItems']['edges']
                    for line_item in line_items:
                        product_name = line_item['node']['title']
                        quantity = line_item['node']['quantity']
                        price = line_item['node']['originalTotalSet']['shopMoney']['amount']
                        total_price = float(price) * quantity

                        # Check if product already exists in product_data dictionary
                        if product_name in product_data:
                            # Update the existing product's price and order count
                            product_data[product_name]['total_price'] += total_price
                            product_data[product_name]['order_count'] += 1
                        else:
                            # Add a new product to the product_data dictionary
                            product_data[product_name] = {
                                'total_price': total_price,
                                'order_count': 1
                            }
                print(product_data)
                has_next_page = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('hasNextPage', False)
                end_cursor = data.get('data', {}).get('orders', {}).get('pageInfo', {}).get('endCursor', None)
                time.sleep(5)  # Add a delay to avoid rate limiting

                result = update_product_data(user.id, product_data)
                return result
            except Exception as e:
                print(f"Error fetching orders: {e}")

    
def update_product_data(user_id, product_data):
        for key, value in product_data.items():
                daily_order = value["order_count"]
                daily_price = value["total_price"]
                print(f"Key: {key}, Order Count: {daily_order}, Total Price: {daily_price}")

                conn = db.db_connect()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE name = %s AND userid = %s", (key, user_id))
                existing_data = cursor.fetchone()

                if existing_data:
                    cursor.execute("UPDATE products SET tcost = tcost + %s, torder = torder + %s  WHERE date = %s", (daily_price, daily_order))
                else:
                    return "Product not found"
                
        return "Products data updated successfully."


