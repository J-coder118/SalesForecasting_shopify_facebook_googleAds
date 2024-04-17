from app.api.keys import bp
from flask import jsonify, request
from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.db.user import User
from app.extensions import db
from dotenv import dotenv_values, set_key
from app.cron.shopify import fetch_all_shopify_data, fetch_product_data
from app.cron.facebook import fetch_all_facebook_data
from app.cron.google import fetch_total_googleAds_data

env_vars = dotenv_values()

@bp.route('/shopify_key', methods=['POST'])
@jwt_required()
def shopify_key():
    try:
        user_id = get_jwt_identity()
        sh_domain = request.form.get('sh_domain')
        sh_token = request.form.get('sh_token')

        if not (sh_token and sh_domain):
            return jsonify(message='Missing API keys'), 400
        
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='User not found'), 404
        
        # if user.sh_api != '' and user.sh_api_key != '' and user.sh_token != '' and user.sh_secret_key != '':
        #     return jsonify(message='You have already registered shopify key'), 400
        # else:
        user.sh_domain = sh_domain
        user.sh_token = sh_token
        
        db.session.commit()

        fetch_all_shopify_data(user)      
        fetch_product_data(user)      
        return jsonify(message='API keys added successfully and fetch the shopify data...'), 200
    except Exception as e:
        return jsonify({'error_shopify_key': str(e)})
    
    
@bp.route('/facebook_ads_key', methods=['POST'])
@jwt_required()
def facebook_key():
    try:
        user_id = get_jwt_identity()
        fb_ads_account_id = request.form.get('fb_ads_account_id')
        

        if not fb_ads_account_id:
                return jsonify(message='Missing API keys'), 400
            
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='User not found'), 404
        
        user.fb_ads_account_id = fb_ads_account_id
            
        db.session.commit()

        fetch_all_facebook_data(user.fb_ads_account_id, user_id)
        return jsonify(message='API keys added successfully'), 200
    except Exception as e:
        return jsonify({'error_facebook': str(e)})


@bp.route('/google_ads_key', methods=['POST'])
@jwt_required()
def google_key():
    try:
        user_id = get_jwt_identity()
        gg_mmc_id = request.form.get('gg_mmc_id')
        gg_ads_account_id = request.form.get('gg_ads_account_id')
        start_date = request.form.get('start_date')

        if not (gg_mmc_id and gg_ads_account_id):
                return jsonify(message='Missing API keys'), 400
            
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='User not found'), 404
        
        user.gg_mmc_id = gg_mmc_id
        user.gg_ads_account_id = gg_ads_account_id
        db.session.commit()
        
        fetch_total_googleAds_data(user.gg_mmc_id, user.gg_ads_account_id, user_id, start_date)
        return jsonify(message='API keys added successfully'), 200
    except Exception as e:
        return jsonify({'error_google': str(e)})


