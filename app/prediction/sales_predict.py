from flask import Flask, jsonify, request
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.models import load_model

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler

from keras.models import Sequential
from keras.layers import LSTM, Dense

from app.db.sales import Sales
from app.db.ads import Ads

import os
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta

def monthly_sales(data):
    """Returns a dataframe where each row represents total sales for a given
    month. Columns include 'date' by month and 'sales'.
    """
    monthly_data = data.copy()
    # Drop the day indicator from the date column
    monthly_data.date = monthly_data.date.apply(lambda x: str(x)[:-3])
    # Sum sales per month
    monthly_data = monthly_data.groupby('date')['sales'].sum().reset_index()
    monthly_data.date = pd.to_datetime(monthly_data.date)
    monthly_data.to_csv('../data/monthly_data.csv')

    return monthly_data


def check_model():
    try:
        file_path = "model/Sales_model.h5"

        # Get the time of the last modification of the file in seconds since the epoch
        file_mtime = os.path.getmtime(file_path)

        # Convert the time in seconds to a datetime object
        file_modification_date = datetime.datetime.fromtimestamp(file_mtime).date()

        # Get today's date
        today_date = datetime.date.today()

        # Compare the file modification date with today's date
        if file_modification_date == today_date:
            return jsonify({'status': 'The model is up-to-date.'}), 200
        elif file_modification_date < today_date:
            store_sales = Sales.load_sales(Sales)
            ads_data_predict = Ads.load_ads_predict(Ads, "2022-01-01")
            generate_model(store_sales, ads_data_predict)
            return jsonify({'status': 'The model updated.'}), 200
        
    except Exception as e:
        return jsonify({'errors': str(e)})

def generate_model():
    try:
       
            store_sales = Sales.load_sales(Sales)
            ads_data_predict = Ads.load_ads_predict(Ads, "2022-01-01")
            print("==========================================================================")
            print("-----------------------------------------------------------------------------------model update")
            new_data = {
            'date': pd.date_range(start='2024-01-18', end=datetime.today().date()),
            'fb_ads': 0.0,
            'gg_ads': 0.0
            }
            new_df = pd.DataFrame(new_data)

            # Concatenate the new data with the existing DataFrame
            combined_df = pd.concat([ads_data_predict, new_df]).reset_index(drop=True)
            result =  pd.merge(store_sales, combined_df, on='date')

            result = result[['date', 'orders', 'fb_ads', 'gg_ads', 'total_sales']]
            print("result", result)
            
            dates = result.index
            X = result.iloc[:, 1:4]
            Y = result.iloc[:, 4]

            print("X", X, "Y", Y)

                #Split train and test
            X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, shuffle=True)

            #Count features for modelization
            X_num_columns= len(X.columns)

            #Define model
            model = Sequential()

            model.add(Dense(300,
                            activation='relu',
                            input_dim = X_num_columns))

            model.add(Dense(90,
                            activation='relu'))
            model.add(Dropout(0.2))

            model.add(Dense(30,
                            activation='relu'))
            model.add(Dropout(0.2))

            model.add(Dense(7,
                            activation='relu'))
            model.add(Dropout(0.2))

            model.add(Dense(1,
                            activation='linear'))

            model.compile(optimizer='adam', loss='mean_squared_error')
            print("Model Created")

            #Fit model to training data
            model.fit(X_train, y_train, epochs=5000, batch_size=100)
            print("Training completed")

            model_dir = ""
            model_path = os.path.join(model_dir, "model/Sales_model.h5")

            # Check if the model directory exists, if not, create it
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)

            # Save the model to the specified directory
            model.save(model_path)
            #Save trained model
            # model.save("Sales_model.h5")
            print("Sales_model.h5 saved model to disk in ",os.getcwd())
            return jsonify({'status': 'The model generated.'}), 200
    except Exception as e:
        return jsonify({'errors': str(e)})   

def predict_before_data(store_sales, ads_data_predict, num_days, last_db_date, user_id):
    try:
        # print("0", num_days)
        # new_data = {
        # 'date': pd.date_range(start='2024-01-18', end=datetime.today().date()),
        # 'fb_ads': 0.0,
        # 'gg_ads': 0.0
        # }
        # new_df = pd.DataFrame(new_data)
        # print("1")
        # # Concatenate the new data with the existing DataFrame
        # combined_df = pd.concat([ads_data_predict, new_df]).reset_index(drop=True)
        # result =  pd.merge(store_sales, combined_df, on='date')

        result =  pd.merge(store_sales, ads_data_predict, on='date')
        print("2-=-=============================================================", num_days)
        result = result[['date', 'orders', 'fb_ads', 'gg_ads', 'total_sales']]
        dates = result.index

        print("result", result)
        df_newDates = pd.concat([result.iloc[-(num_days-2):, 1:4]], axis=1)
        #Predict upcoming sales using trained model and imported upcoming dates
        print(f"model/Sales_model_{user_id}.h5")
        model = load_model(f'model/Sales_model_{user_id}.h5')
        Predicted_sales = model.predict(df_newDates)
        act_sales = store_sales['total_sales'][-(num_days-2):].to_list()###12-
        print("here-=-=", Predicted_sales)
        result = []
        for i, predict_data in enumerate(Predicted_sales):
            act_sales_data = act_sales[i]
            previous_data = last_db_date - timedelta(days=(num_days-i))
            previous_date_str = previous_data.strftime('%Y-%m-%d')

            print("test data", previous_date_str, int(np.float64(predict_data[0]).item()), act_sales_data)
            result.append({'date': previous_date_str, 'predict_sales_data': int(np.float64(predict_data[0]).item()), 'act_sales_data': act_sales_data})

        print("predict----", result)
        return result

    except Exception as e:
            return jsonify({'error': str(e)})
    
def predict_by_ads(order, fb_ads, gg_ads, user_id):
    try:
        o = pd.Series([float(order)])
        f = pd.Series([float(fb_ads)])
        g = pd.Series([float(gg_ads)])

        df_newDates = pd.concat([o, f, g]).reset_index(drop=True)
        model = load_model(f'model/Sales_model_{user_id}.h5')

        # Reshape the input data
        input_data = np.array(df_newDates).reshape(1, -1)
        Predicted_sales = model.predict(input_data)

        df = pd.DataFrame(Predicted_sales)
        df.to_csv('newpredict.csv', index=False)
        
        return Predicted_sales
    except Exception as e:
        return jsonify({'errors': str(e)})

        
def predict_future_data(store_sales, last, end):
    try:
        # start_date = '2021-01-01'
        # end_date = '2024-02-09'
        # filtered_data = store_sales[(store_sales['date'] >= start_date) & (store_sales['date'] <= end_date)]

        # Extract the 'total_sales' column
        sales_data = store_sales['total_sales'].values.reshape(-1, 1)

        # Standardize the data
        scaler = StandardScaler()
        sales_data_standardized = scaler.fit_transform(sales_data)

        # Prepare data for LSTM model
        def create_sequences(data, seq_length):
            sequences, labels = [], []
            for i in range(len(data) - seq_length):
                seq = data[i:i + seq_length]
                label = data[i + seq_length]
                sequences.append(seq)
                labels.append(label)
            return np.array(sequences), np.array(labels)

        seq_length = 10  # Adjust as needed
        X, y = create_sequences(sales_data_standardized, seq_length)

        # Reshape the data for LSTM (samples, time steps, features)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Define the LSTM model
        model = Sequential()
        model.add(LSTM(50, activation='relu', input_shape=(seq_length, 1)))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')

        # Train the model on the entire dataset
        model.fit(X, y, epochs=50, batch_size=32)

        # Make predictions for the future dates
        future_dates = pd.date_range(start=last, end=end, freq='D')

        # Extract the last seq_length days from the training data
        last_sequence = sales_data_standardized[-seq_length:].reshape((1, seq_length, 1))

        # Predict future sales day by day
        predicted_sales = []

        for _ in range(len(future_dates)):
            predicted_sales_standardized = model.predict(last_sequence)
            predicted_sales.append(predicted_sales_standardized.flatten()[0])

            # Update the sequence for the next prediction
            last_sequence = np.roll(last_sequence, -1, axis=1)
            last_sequence[0, -1, 0] = predicted_sales_standardized

        # Inverse transform the predicted sales
        predicted_sales = scaler.inverse_transform(np.array(predicted_sales).reshape(-1, 1))

        # Display the predicted sales for each day
        predicted_df = pd.DataFrame({'Date': future_dates, 'Predicted_Sales': predicted_sales.flatten()})
        print(predicted_df)

        result = []
        for index, row in predicted_df.iterrows():
            date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
            result.append({'date': date, 'predict_sales_data': row['Predicted_Sales']})
        print(result)
        return result

    except Exception as e:
            return jsonify({'error': str(e)})
    


def predict_by_tf(store_sales, ads_data_predict, user_id):
    # new_data = {
    # 'date': pd.date_range(start='2024-01-18', end=datetime.today().date()),
    # 'fb_ads': 0.0,
    # 'gg_ads': 0.0
    # }
    # new_df = pd.DataFrame(new_data)

    # # Concatenate the new data with the existing DataFrame
    # combined_df = pd.concat([ads_data_predict, new_df]).reset_index(drop=True)

    result =  pd.merge(store_sales, ads_data_predict, on='date')
    result = result[['date', 'orders', 'fb_ads', 'gg_ads', 'total_sales']]

    result.to_csv('output.csv', index=False)
    print("result", result)
    
    dates = result.index

    X = result.iloc[:, 1:4]
    Y = result.iloc[:, 4]

    print("X", X, "Y", Y)
 
        #Split train and test
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, shuffle=True)

    #Count features for modelization
    X_num_columns= len(X.columns)

    #Define model
    model = Sequential()

    model.add(Dense(300,
                    activation='relu',
                    input_dim = X_num_columns))

    model.add(Dense(90,
                    activation='relu'))
    model.add(Dropout(0.2))

    model.add(Dense(30,
                    activation='relu'))
    model.add(Dropout(0.2))

    model.add(Dense(7,
                    activation='relu'))
    model.add(Dropout(0.2))

    model.add(Dense(1,
                    activation='linear'))

    model.compile(optimizer='adam', loss='mean_squared_error')
    print("Model Created")

    #Fit model to training data
    model.fit(X_train, y_train, epochs=5000, batch_size=100)
    print("Training completed")

    #Save trained model
    model.save("Sales_model_{user_id}.h5")
    print("Sales_model.h5 saved model to disk in ",os.getcwd())

    #1.accuracy,
    #Predict known daily sales in order to check results
    predictions = model.predict(X)
    predictions_list = map(lambda x: x[0], predictions)
    predictions_series = pd.Series(predictions_list,index=dates)
    dates_series =  pd.Series(dates)

    print("predictions_list", predictions_list)
    df_newDates = pd.concat([result.iloc[-30:, 1:4]], axis=1)
    #Predict upcoming sales using trained model and imported upcoming dates
    model = load_model(f'Sales_model_{user_id}.h5')
    Predicted_sales = model.predict(df_newDates)
    #Export predicted sales
    new_dates_series=pd.Series(df_newDates.index)
    new_predictions_list = map(lambda x: x[0], Predicted_sales)
    new_predictions_series = pd.Series(new_predictions_list,index=new_dates_series)
    new_predictions_series.to_csv("predicted_sales1.csv")

   