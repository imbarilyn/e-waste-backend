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
    if response.status_code == 201:

        return True
    return False
#
