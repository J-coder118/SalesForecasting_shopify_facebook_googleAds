from flask import Flask
from flask_cors import CORS
from config import Config
from flask_apscheduler import APScheduler
from flask_jwt_extended import create_access_token, JWTManager
from datetime import datetime, timedelta
from app.db import database as db
from app.extensions import db
from app.cron.shopify import fetch_daily_shopify_data, fetch_daily_product_data
from app.cron.facebook import fetch_daily_facebook_data
from app.cron.google import fetch_daily_googleAds_data
from app.prediction.sales_predict import generate_model
from app.db.user import User
import logging
import sys, os

jwt = JWTManager()

def initialize_jwt(app):
    jwt.init_app(app)

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)
    app.config['JWT_SECRET_KEY'] = os.environ.get('jwt_secret_key')
    db.init_app(app)
    jwt.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api.sales import bp as sales_bp
    app.register_blueprint(sales_bp,  url_prefix='/v1/api/sales')

    from app.api.orders import bp as orders_bp
    app.register_blueprint(orders_bp,  url_prefix='/v1/api/orders')

    from app.api.auth import bp as auth_bp
    app.register_blueprint(auth_bp,  url_prefix='/v1/api/auth')

    from app.api.keys import bp as keys_bp
    app.register_blueprint(keys_bp,  url_prefix='/v1/api/keys')

    from app.api.upload import bp as upload_bp
    app.register_blueprint(upload_bp,  url_prefix='/v1/api/upload')
    class Config(object):
        pass
    app.config.from_object(Config())

    @app.before_request
    def schedule_jobs():
        with app.app_context():
            daily_functions = {
                'shopify': fetch_daily_shopify_data,
                'facebook': fetch_daily_facebook_data,
                'google': fetch_daily_googleAds_data,
                'product': fetch_daily_product_data
            }
            users = User.query.all()
            JOBS = []
            for user in users:
                for store in daily_functions:
                    job = {
                        'id': f'job_{user.id}_{store}',
                        'func': daily_functions[store],
                        'trigger': 'interval',
                        'seconds': 24 * 60 * 60,  # Every 24 hours
                        'args': (user,)  # Pass the user ID and additional argument as a tuple
                    }
                    JOBS.append(job)
                else:
                    print(f"No function assigned for user: {user}")

            # Start the scheduler after defining the jobs
            scheduler = APScheduler()
            scheduler.init_app(app)
            scheduler.start()

    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.ERROR)

    return app
    #     daily_functions = {
    #         'shopify': fetch_daily_shopify_data,
    #         'facebook': fetch_daily_facebook_data,
    #         'google': fetch_daily_googleAds_data,
    #         'product': fetch_daily_product_data
    #     }
    #     users = User.query.all()
    #     JOBS = []
    #     for user in users:
    #         for store in daily_functions:
    #             job = {
    #                 'id': f'job_{user.id}_{store}',
    #                 'func': daily_functions[store],
    #                 'trigger': 'interval',
    #                 'seconds': 24 * 60 * 60,  # Every 24 hours
    #                 'args': (user)  # Pass the user ID and additional argument as a tuple
    #             }
    #             JOBS.append(job)
    #         else:
    #             print(f"No function assigned for user: {user}")


    # app.config.from_object(Config())
    # scheduler = APScheduler()
    # scheduler.init_app(app)
    # scheduler.start()

    # app.logger.addHandler(logging.StreamHandler(sys.stdout))
    # app.logger.setLevel(logging.ERROR)

    # return app



