from app.api.orders import bp
from flask import jsonify, request
from datetime import datetime, timedelta
from app.prediction import orders_predict as op
from app.db.user import User
from app.db.sales import Sales
from flask_jwt_extended import get_jwt_identity, jwt_required

@bp.route('/', methods = ['POST', 'OPTIONS'])
# @jwt_required()
def index():
    try:
        print("orders-=-=-=-=-=-=-=-=-=")
        # user_id = get_jwt_identity()
        username = request.form.get('username')
        print("username", username)
        user = User.query.filter_by(username=username).first()
        predict_future_result = ""
        predict_before_result = ""
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        store_sales = Sales.load_sales(Sales, user.id)
        last_db_date = Sales.query.order_by(Sales.id.desc()).first().date
        if (last_db_date - start_date).days < 0:
            predict_future_result = op.predict_future_data(store_sales, (end_date - last_db_date).days, last_db_date)
            return jsonify({
            'status': "success",
            'response': {
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
                predict_before_result = op.predict_before_data(store_sales, (last_db_date - start_date).days) 
                return jsonify({
                    'status': "success",
                    'response': {
                                    "predict_before_data": predict_before_result,
                                    "predict_future_data": None
                                },#
                    "date": {
                        "start_date": start,
                        "end_date": end
                    } 
                })
            else:
                print("2")
                next_date = last_db_date + timedelta(days=1)
                next_db_date = next_date.strftime("%Y-%m-%d")
                predict_before_result = op.predict_before_data(store_sales, (last_db_date - start_date).days)
                next_db_date = datetime.strptime(next_db_date, "%Y-%m-%d")
                predict_future_result = op.predict_future_data(store_sales, (end_date - last_db_date).days, next_db_date)

                return jsonify({
                    'status': "success",
                    'response': {
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

