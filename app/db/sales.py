from app.extensions import db
import pandas as pd
from app.db.user import User

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime)
    total_sales = db.Column(db.Float)
    orders = db.Column(db.Integer)

    user = db.relationship('User', backref='sales')

    def __repr__(self):
        return f'Sales(id={self.id}, date={self.date}, total_sales={self.total_sales}, orders={self.orders})'
    
    def load_sales(self, user_id):
        store_sales = self.query.filter_by(userid=user_id).all()

        data_dict = {
            "date": [ss.date for ss in store_sales],
            "total_sales": [ss.total_sales for ss in store_sales],
            "orders": [ss.orders for ss in store_sales]
        }
        df = pd.DataFrame(data_dict)

        filtered_data = df.loc[:, ['date', 'total_sales', 'orders']]
        return filtered_data

