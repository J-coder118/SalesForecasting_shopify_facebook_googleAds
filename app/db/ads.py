from app.extensions import db
import pandas as pd
from datetime import datetime

class Ads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    fb_ads = db.Column(db.Float)
    gg_ads = db.Column(db.Float)
    shopify = db.Column(db.Float)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'Ads(id={self.id}, date={self.date}, fb_ads={self.fb_ads}, gg_ads={self.gg_ads}, shopify={self.shopify}, userid={self.userid})'
    
    def load_ads(self, start_date, end_date, userid=None):
        ads_data = self.query.filter(self.date.between(start_date, end_date), self.userid == userid).all()
        data_dict = {
            "date": [ad.date for ad in ads_data],
            "fb_ads": [ad.fb_ads for ad in ads_data],
            "gg_ads": [ad.gg_ads for ad in ads_data],
            "shopify": [ad.shopify for ad in ads_data],
            "userid": [ad.userid for ad in ads_data]
        }

        df = pd.DataFrame(data_dict)
        df = df.sort_values(by='date') 

        filtered_data = df.loc[:, ['date', 'fb_ads', 'gg_ads']]
        
        result = []
        for index, row in filtered_data.iterrows():
            if pd.isnull(row['fb_ads']):
                row['fb_ads'] = 0
            if pd.isnull(row['gg_ads']):
                row['gg_ads'] = 0
            data = {
                "date": row['date'].strftime('%Y-%m-%d'),
                "facebook_ads": row['fb_ads'],
                "google_ads": row['gg_ads']
            }
            result.append(data)

        return result
    
    def load_ads_predict(self, start_date, userid=None):
        last_date = datetime.now() 
        ads_data = self.query.filter(self.date.between(start_date, last_date), self.userid == userid).order_by(self.date).all()
        
        data_dict = {
            "date": [ad.date for ad in ads_data],
            "fb_ads": [ad.fb_ads for ad in ads_data],
            "gg_ads": [ad.gg_ads for ad in ads_data],
            "shopify": [ad.shopify for ad in ads_data]
        }

        df = pd.DataFrame(data_dict)

        filtered_data = df.loc[:, ['date', 'fb_ads', 'gg_ads']]

        return filtered_data