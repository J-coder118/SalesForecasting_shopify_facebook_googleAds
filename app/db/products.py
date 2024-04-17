from app.extensions import db
import pandas as pd
class Products(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable=False)
    tcost = db.Column(db.Integer)
    torder = db.Column(db.Integer)
    userid = db.Column(db.Integer)
   


    def __repr__(self):
        return f'User(id={self.id}, name={self.name}, total_cost={self.tcost}, total_orders={self.torder}, userid={self.userid})'


    def load_sales(self, user_id):
        products_sales = self.query.filter_by(userid=user_id).all()

        data_dict = {
            "name": [ss.name for ss in products_sales],
            "total_cost": [ss.tcost for ss in products_sales],
            "total_orders": [ss.torder for ss in products_sales]
        }
        df = pd.DataFrame(data_dict)

        filtered_data = df.loc[:, ['name', 'total_cost', 'total_orders']]
        return filtered_data