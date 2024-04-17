from app.api.auth import bp
from flask import jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.cron.shopify import fetch_product_data
from app.db.user import User
from app.db.sales import Sales
from app.db.ads import Ads
from app.extensions import db
from dotenv import dotenv_values, set_key

env_vars = dotenv_values()


@bp.route('/register', methods = ['POST'])
def register():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        if User.query.filter_by(username=username).first():
            return jsonify(message='Username already exists'), 409

        if User.query.filter_by(email=email).first():
            return jsonify(message='Email already exists'), 409
        
        if User.query.filter_by(phone=phone).first():
            return jsonify(message='Phone number already exists'), 409

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_password, phone=phone, sh_domain="", sh_token="", fb_ads_account_id="", gg_mmc_id="", gg_ads_account_id="")
        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username=username).first()
        return jsonify(message='User registered successfully and saved all products data'), 201
    except Exception as e:
        return jsonify({"error_register": str(e)})


@bp.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify(message='Invalid username or password'), 401

        access_token = create_access_token(identity=user.id)

        store_sales = Sales.query.filter_by(userid=user.id).all()
        ads = Ads.query.filter_by(userid=user.id).all()
        key_status = {
            'sh_domain': user.sh_domain,
            'sh_token': user.sh_token,
            'fb_ads_account_id': user.fb_ads_account_id,
            'gg_mmc_id': user.gg_mmc_id,
            'gg_ads_account_id': user.gg_ads_account_id,
            'sales_db_status': len(store_sales) > 0,
            'facebook_db_status': len(ads) > 0,
            'google_db_status': len(ads) > 0
            }
        
        return jsonify({'access_token': access_token, 'key_status': key_status}), 200
        
    except Exception as e:
        return jsonify({"error_login": str(e)})


@bp.route('/protected', methods=['POST'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(id=user.id, username=user.username, email=user.email), 200


@bp.route('/profile', methods=['POST'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(username=user.username, email=user.email, phone=user.phone), 200



@bp.route('/password', methods=['POST'])
@jwt_required()
def password():
    password = request.form.get('password')
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or not check_password_hash(user.password, password):
            return jsonify(message='Invalid username or password'), 401

    return jsonify(message='success'), 200


@bp.route('/re_register', methods = ['POST'])
@jwt_required()
def re_register():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        current_user_id = get_jwt_identity()
        hashed_password = generate_password_hash(password)

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)


        user.username = username
        user.email = email
        user.password = hashed_password
        user.phone = phone

        db.session.commit()
        
        return jsonify(message='User info updated successfully and saved all products data'), 201
        
    except Exception as e:
        return jsonify({"error_register": str(e)})
    

@bp.route('/k_d_status', methods=['POST'])
@jwt_required()
def status():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        store_sales = Sales.query.filter_by(userid=user.id).all()
        ads = Ads.query.filter_by(userid=user.id).all()
        key_status = {
            'sh_domain': user.sh_domain,
            'sh_token': user.sh_token,
            'fb_ads_account_id': user.fb_ads_account_id,
            'gg_mmc_id': user.gg_mmc_id,
            'gg_ads_account_id': user.gg_ads_account_id,
            'sales_db_status': len(store_sales) > 0,
            'facebook_db_status': len(ads) > 0,
            'google_db_status': len(ads) > 0
            }
        
        return jsonify({'key_status': key_status}), 200
        
    except Exception as e:
        return jsonify({"error_login": str(e)})








