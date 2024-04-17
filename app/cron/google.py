from google.ads.googleads.client import GoogleAdsClient
from app.db import database as db
import datetime

def get_daily_spend(client, customer_id, start_date, end_date):
    # Get the Google Ads API service clients
    google_ads_service = client.get_service('GoogleAdsService')

    # Set the query to retrieve daily spend
    query = f"""
        SELECT
            segments.date,
            campaign.id,
            campaign.name,
            metrics.cost_micros
        FROM
            campaign
        WHERE
            segments.date >= '{start_date}' AND segments.date <= '{end_date}'
        """

    response = google_ads_service.search(query=query, customer_id=customer_id)
    daily_spend = {}
    for row in response:
        date = row.segments.date
        cost_micros = row.metrics.cost_micros
        if date in daily_spend:
            daily_spend[date] += cost_micros / 1000000
        else:
            daily_spend[date] = cost_micros / 1000000

    return daily_spend

def fetch_total_googleAds_data(gg_mmc_id, gg_ads_account_id, user_id, start_date):
    client = GoogleAdsClient.load_from_storage('google-ads.yaml', login_customer_id=gg_ads_account_id)
    end_date = datetime.datetime.now().strftime('%Y-%m-%d') 
    result = get_daily_spend(client, gg_mmc_id, start_date, end_date)
    conn = db.db_connect()
    cursor = conn.cursor()
    for key, value in result.items():
        print("Key:", key)
        print("Value:", value)
        cursor.execute("INSERT INTO ads (date, gg_ads, userid) VALUES (%s, %s, %s)",
                                    (key, value, user_id))


def fetch_daily_googleAds_data(user):
    client = GoogleAdsClient.load_from_storage('google-ads.yaml', login_customer_id=user.gg_ads_account_id)
  
    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d') 
    result = get_daily_spend(client, user.gg_mmc_id, start_date, end_date)

    conn = db.db_connect()
    cursor = conn.cursor()

    for key, value in result.items():
        print("Key:", key)
        print("Value:", value)
        cursor.execute("SELECT * FROM ads WHERE date = %s AND userid = %s", (key, user.id))
        existing_data = cursor.fetchone()
        if existing_data:
            print(f"Data for {key} already exists. Skipping insertion.")
        else:
            cursor.execute("INSERT INTO ads (date, gg_ads, userid) VALUES (%s, %s, %s)",
                                    (key, value, user.id))
    conn.commit()
    print("google data fetched and updated")

