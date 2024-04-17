from app.api.sales import bp
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import datetime, timedelta
from app.prediction import sales_predict as sp
from app.cron.shopify import fetch_all_shopify_data
from app.db.user import User
from app.db.sales import Sales
from app.db.ads import Ads
from app.db.products import Products
import pandas as pd


@bp.route('/', methods = ['GET', 'POST', 'OPTIONS'])
# @jwt_required()
def index():
    try:
        # user_id = get_jwt_identity()
        predict_future_result = ""
        predict_before_result = ""
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        ads_data = Ads.load_ads(Ads, start, end, user.id)
        ads_data_predict = Ads.load_ads_predict(Ads, "2022-01-01", user.id)
        store_sales = Sales.load_sales(Sales, user.id)
        last_db_date = Sales.query.order_by(Sales.id.desc()).first().date
        # result = sp.predict_by_tf(store_sales, ads_data_predict, user.id)
        ads_data_predict.fillna(value=0, inplace=True)
        print("result")
        if store_sales.empty:
            return jsonify({'status': "fail",
                            'response': "No data found in the database"}), 404
        else:
            if (last_db_date - start_date).days < 0:
                predict_future_result = sp.predict_future_data(store_sales, last_db_date, end_date)
                return jsonify({
                'status': "success",
                'response': {
                                "ads": ads_data,
                                "predict_before_data": None,
                                "predict_future_data": predict_future_result
                            },
                "date": {
                    "start_date": start,
                    "end_date": end
                } 
            })
            else:
                if (last_db_date - end_date).days >= 0:
                    predict_before_result = sp.predict_before_data(store_sales, ads_data_predict, (last_db_date - start_date).days, last_db_date, user.id) 
                    return jsonify({
                        'status': "success",
                        'response': {
                                        "ads": ads_data,
                                        "predict_before_data": predict_before_result,
                                        "predict_future_data": None
                                    },#
                        "date": {
                            "start_date": start,
                            "end_date": end
                        } 
                    })
                else:
                    predict_before_result = sp.predict_before_data(store_sales, ads_data_predict, (last_db_date - start_date).days, last_db_date, user.id)
                    predict_future_result = sp.predict_future_data(store_sales, last_db_date, end_date)
                    return jsonify({
                        'status': "success",
                        'response': {
                                        "ads": ads_data,
                                        "predict_before_data": predict_before_result,
                                        "predict_future_data": predict_future_result
                                    },
                        "date": {
                            "start_date": start,
                            "end_date": end
                        } 
                    })
    except Exception as e:
        return jsonify({'error': str(e)})

@bp.route('/ads', methods = ['POST', 'OPTIONS'])
@jwt_required()
def ads():
    try: 
        user_id = get_jwt_identity()
        picked_date_str = request.form.get('picked_date')
        facebook_ads = request.form.get('fb_ads')
        google_ads = request.form.get('gg_ads')
        order = request.form.get('order')
        picked_date = datetime.strptime(picked_date_str, "%Y-%m-%d")
        predict_by_ADS = sp.predict_by_ads(order, facebook_ads, google_ads, user_id)#, (last_db_date - start_date).days)#(picked_date - last_db_date).days, next_db_date, user_changes)
        model = sp.generate_model()
        return jsonify({
                'status': "success",
                'response': {'data': round(float(predict_by_ADS[0][0]), 2)}
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})
    

@bp.route('/fetch_all_data', methods = ['POST', 'OPTIONS'])
@jwt_required()
def fetch_all_data():
    user_id = get_jwt_identity()
    result = fetch_all_shopify_data(user_id)

    if result == "success":
        return jsonify({
                'status': "success",
                'response': "Data has been fetched."
        })
    else:
        return jsonify({
            'status': "failed",
            'response': "error occured."
        })
    
@bp.route('/fetch_total_data', methods = ['POST', 'OPTIONS'])
@jwt_required()
def fetch_total_data():
    try:
        user_id = get_jwt_identity()
        ads_data_predict = Ads.load_ads_predict(Ads, "2022-01-01", user_id)
        store_sales = Sales.load_sales(Sales, user_id)

        if store_sales.empty:
                return jsonify({'status': "fail",
                                'response': "No data found in the storeSales database"}), 404
        if ads_data_predict.empty:
                return jsonify({'status': "fail",
                                'response': "No data found in the ads data database"}), 404

        store_sales_result = []
        for index, row in store_sales.iterrows():
            date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
            store_sales_result.append({'date': date, 'total_sales': row['total_sales'], 'total_orders': row['orders']})
        
        ads_data_result = []
        for index, row in ads_data_predict.iterrows():
            date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
            
            if pd.isnull(row['fb_ads']):
                ads_data_predict.at[index, 'fb_ads'] = 0
            if pd.isnull(row['gg_ads']):
                ads_data_predict.at[index, 'gg_ads'] = 0

            ads_data_result.append({'date': date, 'fb_ads': ads_data_predict.at[index, 'fb_ads'], 'gg_ads': ads_data_predict.at[index, 'gg_ads']})
        return jsonify({
            'status': "success",
            'response': {
                "store_sales": store_sales_result,
                "ads_data": ads_data_result
            }
        })
    except Exception as e:
        return jsonify({'error_fetch_total_data': str(e)})
    


@bp.route('/fetch_product_data', methods = ['POST', 'OPTIONS'])
@jwt_required()
def fetch_product_data():
    try:
        user_id = get_jwt_identity()
        
        product_data = Products.load_sales(Products, user_id)

        if product_data.empty:
                return jsonify({'status': "fail",
                                'response': "No data found in the product data database"}), 404
       
        product_data_result = []
        for index, row in product_data.iterrows():
            product_data_result.append({'name': row['name'], 'total_cost': row['total_cost'], 'total_orders': row['total_orders']})
        
        return jsonify({
            'status': "success",
            'response': {
                "products_data": product_data_result
            }
        })
    except Exception as e:
        return jsonify({'error_fetch_total_data': str(e)})



    


    