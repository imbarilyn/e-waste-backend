from pathlib import Path
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
import requests

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

def sync_with_woocommerce(product: Product):
    payload = {
        "name": product.name,
        "type": product.stock_type,
        "regular_price": product.regular_price,
        "short_description": product.short_description,
        # "images": [{"src": url} for url in product.images],
        "images": [{"src": "https://recommerce.mzawadi.com/wp-content/uploads/2025/02/T_2_back.jpg"}],
        "stock_quantity": product.stock_quantity,
        "meta_data": [{"key": "unit", "value": product.weight}]
    }

    response = requests.post(f'{woocommerce_api_url}/wp-json/wc/v3/products', json=payload, auth=(woocommerce_consumer_key, woocommerce_consumer_secret))
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
