from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
import hmac
import hashlib
from app.db import database as db
import datetime
from datetime import timedelta
def genAppSecretProof(app_secret, access_token):
    h = hmac.new (
        app_secret.encode('utf-8'),
        msg=access_token.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    return h.hexdigest()
# Set up the Facebook Marketing API
def fetch_all_facebook_data(ad_account_id, user_id):
    app_id = '779000976936602'    # My APP
    app_secret = '68a86037d075765f36dd0915c5e2ceeb'
    access_token = 'EAALEf0yCjpoBOz1MsSNZCXbYw1SsyhCxzwjZBn1tQyTVyPHtJZBJSJZBPWhraUur0zzAROihEnqbKH1N6cSg2U2kCzBSf7A2sn2LEy3DdHcNxgyRa3ZBZA2XZAVAAQ3PzWQDsldYxioh6v3yq1hS d32XWKfXwlyVpHAW0A9YilZCamGVutZAjRYZBjqmkMyp9IldAWyYOpkPF2' # 
    app_secret_proof = genAppSecretProof(app_secret, access_token)
    print(app_secret_proof)

    FacebookAdsApi.init(app_id, app_secret, access_token)

    # Define the fields you want to retrieve
    fields = [
        AdsInsights.Field.spend,
        AdsInsights.Field.date_start,
        AdsInsights.Field.date_stop,
        AdsInsights.Field.campaign_name,
        AdsInsights.Field.created_time,

    ]
    # Set up the Ad Account
    # ad_account_id = 'act_555132662374918'
    ad_account_id = ad_account_id
    ad_account = AdAccount(ad_account_id)
    # Make the API request
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.now().date()
    daily_costs = {}

    # Loop through each day in the date range
    current_date = start_date
    while current_date <= end_date:
        # Set the time range for the current day
        time_range = {
            'since': current_date.strftime('%Y-%m-%d'),
            'until': current_date.strftime('%Y-%m-%d')
        }

        # Set up the params for the API request
        params = {
            'level': 'ad',
            'time_range': time_range
        }

        try:
            insights = ad_account.get_insights(fields=fields, params=params)

            # Sum up the costs for the current day
            total_cost = 0
            for insight in insights:
                total_cost += float(insight[AdsInsights.Field.spend])

            # Store the total cost for the current day in the dictionary
            daily_costs[current_date] = total_cost

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        # Move to the next day
        current_date += timedelta(days=1)

    # Print the daily costs
    conn = db.db_connect()
    cursor = conn.cursor()
    for date, cost in daily_costs.items():
        print(f"Date: {date}")
        print(f"Total Spend: {cost}")
        cursor.execute("INSERT INTO ads (date, fb_ads, userid) VALUES (%s, %s, %s)",
        (date, cost, user_id))
        print("---")


def fetch_daily_facebook_data(user):
    app_id = '779000976936602'    # My APP
    app_secret = '68a86037d075765f36dd0915c5e2ceeb'
    access_token = 'EAALEf0yCjpoBOz1MsSNZCXbYw1SsyhCxzwjZBn1tQyTVyPHtJZBJSJZBPWhraUur0zzAROihEnqbKH1N6cSg2U2kCzBSf7A2sn2LEy3DdHcNxgyRa3ZBZA2XZAVAAQ3PzWQDsldYxioh6v3yq1hS d32XWKfXwlyVpHAW0A9YilZCamGVutZAjRYZBjqmkMyp9IldAWyYOpkPF2' # Jarret Access Token(Graphql)   Shopify Ads 
    
    app_secret_proof = genAppSecretProof(app_secret, access_token)
    print(app_secret_proof)

    FacebookAdsApi.init(app_id, app_secret, access_token)

    # Define the fields you want to retrieve
    fields = [
        AdsInsights.Field.spend,
        AdsInsights.Field.date_start,
        AdsInsights.Field.date_stop,
        AdsInsights.Field.campaign_name,
        AdsInsights.Field.created_time,

    ]
    # Set up the Ad Account
    # ad_account_id = 'act_555132662374918'
    ad_account_id = user.fb_ads_account_id
    ad_account = AdAccount(ad_account_id)
    # Make the API request
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.now().date()
    one_day_back = end_date - timedelta(days=1)
    daily_costs = {}

    # Loop through each day in the date range
    current_date = one_day_back
    while current_date <= end_date:
        # Set the time range for the current day
        time_range = {
            'since': current_date.strftime('%Y-%m-%d'),
            'until': current_date.strftime('%Y-%m-%d')
        }

        # Set up the params for the API request
        params = {
            'level': 'ad',
            'time_range': time_range
        }

        try:
            insights = ad_account.get_insights(fields=fields, params=params)

            # Sum up the costs for the current day
            total_cost = 0
            for insight in insights:
                total_cost += float(insight[AdsInsights.Field.spend])

            # Store the total cost for the current day in the dictionary
            daily_costs[current_date] = total_cost

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        # Move to the next day
        current_date += timedelta(days=1)

    # Print the daily costs
    conn = db.db_connect()
    cursor = conn.cursor()
    for date, cost in daily_costs.items():
        print(f"Date: {date}")
        print(f"Total Spend: {cost}")
        cursor.execute("SELECT * FROM sales WHERE date = %s AND userid = %s", (date, user.id))
        existing_data = cursor.fetchone()
        if existing_data:
            print(f"Data for {date} already exists. Skipping insertion.")
        else:
            cursor.execute("INSERT INTO ads (date, fb_ads, userid) VALUES (%s, %s, %s)",
        (date, cost, user.id))
    conn.commit()
    print("facebook data fetched and updated")