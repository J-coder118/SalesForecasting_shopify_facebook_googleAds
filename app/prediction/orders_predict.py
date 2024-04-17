from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import jsonify
import joblib

def predict_before_data(store_sales, num_days):
    try:
        store_sales['orders_diff'] = store_sales['orders'].diff()
        store_sales = store_sales.dropna()
        supverised_data = store_sales.drop(['date', 'total_sales', 'orders'], axis=1)
        for i in range(1,32):
            col_sup = 'day_' + str(i)
            supverised_data[col_sup] = supverised_data['orders_diff'].shift(i)
        supverised_data = supverised_data.dropna().reset_index(drop=True)
        train_data = supverised_data[:-1]
        test_data = supverised_data[-num_days-1:]
        scaler = MinMaxScaler(feature_range=(-1,1))
        scaler.fit(train_data)
        train_data = scaler.transform(train_data)
        test_data = scaler.transform(test_data)
        X_train, y_train = train_data[:,1:], train_data[:,0:1]
        X_test, y_test = test_data[:,1:], test_data[:,0:1]
        y_train = y_train.ravel()
        y_test = y_test.ravel()
        sales_dates = store_sales['date'][-num_days-1:].reset_index(drop=True)###
        predict_df = pd.DataFrame(sales_dates)
        act_orders = store_sales['orders'][-(num_days+1):].to_list()###12-
        rf_model = RandomForestRegressor(n_estimators=200, max_depth=20, oob_score=True)
        rf_model.fit(X_train, y_train)
        # joblib.dump(rf_model, 'random_forest_model.pkl')
        rf_pred = rf_model.predict(X_test)
        rf_pred = rf_pred.reshape(-1,1)
        rf_pred_test_set = np.concatenate([rf_pred,X_test], axis=1)
        rf_pred_test_set = scaler.inverse_transform(rf_pred_test_set)
        result_list = []
        for index in range(0, len(rf_pred_test_set)):
            result_list.append(rf_pred_test_set[index][0] + act_orders[index])
        rf_pred_series = pd.Series(result_list, name='rf_pred')
        predict_df = predict_df.merge(rf_pred_series, left_index=True, right_index=True)
        data = np.array(predict_df)
        result = []
        for i, (date, predict_before_data) in enumerate(data):
                act_orders_data = act_orders[i]
                previous_date_str = date.strftime('%Y-%m-%d')
                result.append({'date': previous_date_str, 'predict_order_data': predict_before_data, 'act_order_data': act_orders_data})
        return result
    except Exception as e:
            return jsonify({'error': str(e)})
    

def predict_future_data(store_sales, num_days, start_date):
    try:
        for i in range(1, 32):  # For daily sales forecasting
            store_sales[f'order_lag_{i}'] = store_sales['orders'].shift(i)
        store_sales = store_sales.dropna()
        X = store_sales.drop(['total_sales', 'orders', 'date'], axis=1)
        y = store_sales['orders']
        X_numeric = X.select_dtypes(include=['number'])
        X_datetime = X.select_dtypes(include=['datetime64'])
        X_datetime_numeric = X_datetime.apply(lambda x: x.astype('int64') // 10**9)  # Convert datetime to numerical
        X = pd.concat([X_numeric, X_datetime_numeric], axis=1)
        # Split the data into training and testing sets
        tscv = TimeSeriesSplit(n_splits=5)
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index].reset_index(drop=True), X.iloc[test_index].reset_index(drop=True)
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)

        predict_day_features = pd.concat([X.iloc[-num_days-1:, :]], axis=1)
        predict_day_orders = rf_model.predict(predict_day_features)

        data = np.array(predict_day_orders)
        # Create the desired structure
        result = []
        for i in range(len(data)):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            predict_future_data = data[i]
            result.append({'date': date, 'predict_order_data': predict_future_data, 'act_order_data': None})

        return result
    except Exception as e:
        return jsonify({'error': str(e)})
    
    
