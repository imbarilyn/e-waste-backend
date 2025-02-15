import uuid
from datetime import datetime
from typing import List
import json
from fastapi import APIRouter
from sqlalchemy.orm import Query
from sqlmodel import SQLModel

from app.dependencies import  SessionDependency
import pymysql
from fastapi import Form, UploadFile, File, Depends

from app.woocommerce import sync_with_woocommerce
from main import app
from fastapi.staticfiles import StaticFiles
from secrets import token_hex
import os
from app.auth.auth_aggregator import get_current_active_aggregator



router = APIRouter(
    prefix = '/aggregator',
    tags=['aggregator']
)




@router.post('/upload-images')
async def upload_images(
        file: UploadFile = File(...),
        # aggregator = Depends(get_current_active_aggregator())
):
    from main import app
    required_ext = {'png', 'jpg', 'jpeg'}
    ext = file.filename.split('.')[-1]
    if ext not in required_ext:
        return {
            'message': 'Invalid file format',
            'result': 'fail'
        }, 400
    try:
        os.makedirs('products_images/uploads', exist_ok=True)
        file_name = token_hex(10)
        file_path = os.path.join('products_images/uploads', f"{file_name}.{ext}")

        # Read and write in chunks
        with open(file_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
                url = f'http://127.0.0.1:8000/products_images/uploads/{file_name}.{ext}'
                return {
                    'message': 'File uploaded successfully',
                    'result': 'success',
                    'url': url
                }
    except FileExistsError:
        return {
            'message': 'File already exists',
            'result': 'fail'
        }, 400

class Product(SQLModel):
    name: str
    regular_price: str
    stock_type: str
    short_description: str
    stock_quantity: str
    weight: str
    images: List[str]




@router.post('/add-product/{aggregator_id}')
def add_product(product: Product, aggregator_id: str, db: pymysql.connections.Connection = SessionDependency, aggregator = Depends(get_current_active_aggregator)):
    product_id = str(uuid.uuid4())
    created_at = datetime.now()

    is_sync = sync_with_woocommerce(product)
    # print(f'is_sync: {is_sync}')
    if is_sync:
        try:
            with db.cursor() as cursor:
                query= """
                INSERT INTO products(id, name, regular_price, type, short_description, stock_quantity, weight, images, created_at, aggregator_id)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(query, (product_id, product.name, product.regular_price, product.stock_type, product.short_description, product.stock_quantity, product.weight, json.dumps(product.images),created_at, aggregator_id))
                db.commit()
                return {
                   'message': 'Product added successfully',
                   'result': 'success'
                }

        except Exception as e:
            print(f'Error adding product: {e}')
            db.rollback()
            return {
                'message': 'failed to add product',
                'result': 'fail'
            }
    return {
        'message': 'Failed to sync with woocommerce',
        'result': 'fail'
    }

@router.get('/get-products/{aggregator_id}')
def get_products(aggregator_id: str, limit: int = Query(5) , offset: int = Query(0), all_products: bool = Query(False), db: pymysql.connections.Connection = SessionDependency):
    try:
        with db.cursor() as cursor:
            if all_products:
                query = """
                SELECT * FROM products  WHERE aggregator_id = %s LIMIT 18446744073709551615 OFFSET %s
                """
                cursor.execute(query, (aggregator_id, offset))

            else:
                query = """
                SELECT * FROM products WHERE aggregator_id = %s LIMIT %s OFFSET %s
                """
                cursor.execute(query, (aggregator_id, limit, offset))


            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f'Error fetching prices: {e}')
        cursor.rollback()
        return None
