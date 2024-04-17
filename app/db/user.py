from app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    phone = db.Column(db.String(128), nullable=False)
    sh_domain = db.Column(db.String(128), nullable=True)
    sh_token = db.Column(db.String(128), nullable=True)
    fb_ads_account_id = db.Column(db.String(128), nullable=True)
    gg_mmc_id = db.Column(db.String(128), nullable=True)
    gg_ads_account_id = db.Column(db.String(128), nullable=True)
   


    def __repr__(self):
        return f'User(id={self.id}, username={self.username}, email={self.email}, password={self.password}, phone={self.phone}, sh_api={self.sh_domain}, sh_token={self.sh_token}, fb_ads_account_id={self.fb_ads_account_id}, gg_mmc_id={self.gg_mmc_id}, gg_ads_account_id={self.gg_ads_account_id})'

