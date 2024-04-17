from keras.models import load_model
import pandas as pd
import numpy as np

def predict_by_ads(order, fb_ads, gg_ads):
    try:
        o = pd.Series([order])
        f = pd.Series([fb_ads])
        g = pd.Series([gg_ads])

        df_newDates = pd.concat([o, f, g]).reset_index(drop=True)
        model = load_model('model/Sales_model.h5')

        # Reshape the input data
        input_data = np.array(df_newDates).reshape(1, -1)
        Predicted_sales = model.predict(input_data)
        print("--------", Predicted_sales)

        df = pd.DataFrame(Predicted_sales)
        df.to_csv('newpredict.csv', index=False)
        
        return Predicted_sales
    except Exception as e:
        return print({'errors': str(e)})
    
predict_by_ads(30, 1000, 50)