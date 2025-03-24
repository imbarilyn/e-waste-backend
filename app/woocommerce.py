import json
from pathlib import Path
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
import requests
import pymysql
from app.dependencies import SessionDependency
# from app.routers.aggregator import  Product

current_dir = Path(__file__).resolve().parent if __file__ in locals() else Path.cwd()
env_file = current_dir / '.env'

load_dotenv(env_file)

woocommerce_api_url = os.getenv('WOOCOMMERCE_API_URL')
woocommerce_consumer_key = os.getenv('CONSUMER_KEY')
woocommerce_consumer_secret = os.getenv('CONSUMER_SECRET')
wp_username = os.getenv('WP_USERNAME')
wp_password = os.getenv('WP_PASSWORD')
backend_url = os.getenv('BACKEND_URL')
wp_url = os.getenv('WP_URL')
frontend_url = os.getenv('FRONTEND_URL')

class Product(SQLModel):
    name: str
    stock_type: str
    regular_price: str
    short_description: str
    images: list[str]
    stock_quantity: int
    weight: str
    categories: dict[str, int]
    post_author: str
    dokan_token: str

# def get_pass(product: Product, db: pymysql.connections.Connection = SessionDependency):
#     print(f'product.post_author: {product.post_author}')
#     with db.cursor() as cursor:
#         try:
#             query = """
#              SELECT * FROM e_waste.secrets WHERE dokan_vendor_id = %s
#              """
#             cursor.execute(query, product.post_author)
#             result = cursor.fetchone()
#             # print('result', result)
#             return result
#         except Exception as e:
#             print(f'Error fetching secret pass, {e}')
#             return None

def sync_with_woocommerce(product: Product, db: pymysql.connections.Connection = SessionDependency):
    # Basic auth with woocommerce
    # vendor_credentials = get_pass(product, db)
    # if vendor_credentials is None:
    #     return False
    # username = vendor_credentials['username']
    # password = vendor_credentials['secret_pass']
    #
    # vendor_token = get_vendor_token(username, password)
    # print(f'vendor_token: {vendor_token}')
    # if vendor_token:
    print(f'Product: {product}')
    payload = {
            "name": product.name,
            "type": product.stock_type,
            "regular_price": product.regular_price,
            "short_description": product.short_description,
            # "images": [{"src": url} for url in product.images],
            "images": [{"src": "https://recommerce.mzawadi.com/wp-content/uploads/2025/02/T_2_back.jpg"}],
            "stock_quantity": product.stock_quantity,
            "manage_stock": True,
            "meta_data": [{"key": "unit", "value": product.weight}],
            "categories": [{"id": category_id} for category_id in product.categories.values()],
    }

    response = requests.post(
            f'{woocommerce_api_url}/wp-json/dokan/v1/products/',
            headers={"Authorization": f'Bearer {product.dokan_token}'},    
            json=payload
    )
    print('response', response.json())
    print(f'response {response.json()}')
        # if response.status_code == 201:
        #     return True
    return  True
    # return None

def get_vendor_token(username, password):
    print(f'Vendor user name and password {username} {password}')
    payload = {
        "username": username,
        "password": password
    }
    url = f"{wp_url}/wp-json/jwt-auth/v1/token"
    response = requests.post(url, payload)
    print(f"Response from vendor token: {response.json()['token']}")
    if response.status_code == 200:
        try:
            resp = response.json()
            token = resp['token']
            return token
        except json.JSONDecoder:
            print(f"Failed to decode response f{response.json()}")
            return None
    else:
        print(f"The failed status code is --- {response.json()}")
        return None


# get wordpress token
def get_wp_token():
    payload = {
        "username": wp_username,
        "password": wp_password
    }
    url = f"{wp_url}/wp-json/jwt-auth/v1/token"
    response = requests.post(url, payload)
    if response.status_code == 200:
        try:
            resp = response.json()
            token = resp.get('token')
            return token
        except json.JSONDecoder:
            print(f"Failed to decode response")
            return None
    else:
        print(f"The failed status code is --- {response.status_code}")
        return None






#



