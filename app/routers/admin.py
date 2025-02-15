from fastapi import APIRouter, Depends, Form, Query
import pymysql
from sqlmodel import SQLModel
import uuid


from app.dependencies import SessionDependency
from app.auth.auth_admin import get_active_admin
from app.communication.send_email import send_aggregator_creation_email
from datetime import datetime




router = APIRouter(
    prefix='/admin',
    tags=['admin']
)

# get all the aggregators
@router.get('/get-aggregators/{admin_id}')
def get_aggregators(admin_id: str, db: pymysql.connections.Connection = SessionDependency):
    try:
        with db.cursor() as cursor:
            query = """
             SELECT * FROM aggregators WHERE admin_id = %s        
             """
            cursor.execute(query, admin_id)
            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f'Error fetching aggregators: {e}')
        cursor.rollback()
        return None


@router.get('/get-aggregators/email-communication/{admin_id}')
def get_email_communication(admin_id: str, db: pymysql.connections.Connection = SessionDependency):
    try:
        with db.cursor() as cursor:
            query = """
            SELECT outbox.id, head, body, status, outbox.created_at, full_name, email FROM outbox
            INNER JOIN aggregators ON  outbox.admin_id = %s
            """
            cursor.execute(query, admin_id)
            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f'Error fetching email communication: {e}')
        cursor.rollback()
        return None


@router.post('/resend-email')
def resend_email(
        head: str = Form(...),
        body: str = Form(...),
        aggregator_email: str = Form(...),

):
    print('here in resend')
    print('resending email, head:', {head}, 'body:',{body}, 'aggregator_email:', {aggregator_email})
    is_email_sent = send_aggregator_creation_email(
        head,
        body,
        aggregator_email
    )
    if is_email_sent:
        return {
            'message': 'Email sent successfully',
            'result': 'success'
        }
    return {
        'message': 'Email not sent',
        'result': 'fail'
    }


# @router.post('/set-prices/{admin_id}')
# def set_prices(
#         admin_id: str,
#         regular_price: str = Form(...),
#         name: str = Form(...),
#         weight: str = Form(...),
#         db: pymysql.connections.Connection = SessionDependency,
#         admin: dict = Depends(get_active_admin)
# ):
#     set_product_id = str(uuid.uuid4())
#     created_at = datetime.now()
#
#     try:
#         with db.cursor() as cursor:
#             query = """
#             INSERT INTO product_prices(id, name, regular_price, created_at, admin_id, weight)
#             VALUES(%s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(query, (set_product_id, name, regular_price, created_at, admin_id, weight))
#             db.commit()
#             return {
#                 'message': 'Price updated successfully',
#                 'result': 'success'
#             }
#     except Exception as e:
#         print(f'Error updating price: {e}')
#         db.rollback()
#         return {
#             'message': 'Failed to update price',
#             'result': 'fail'
#         }


@router.get('/get-products/{admin_id}')
def get_products(admin_id: str, limit: int = Query(5), offset: int = Query(0), all_products:bool = Query(False), db: pymysql.connections.Connection = SessionDependency):
    try:
        with db.cursor() as cursor:
            if all_products:
                query = """
                SELECT products.id, name, regular_price, stock_quantity,products.created_at, full_name FROM products
                 LEFT JOIN aggregators ON products.aggregator_id = aggregators.id WHERE admin_id = %s
                 LIMIT 18446744073709551615 OFFSET %s
                """
                cursor.execute(query, (admin_id, offset))
            else:
                query = """
                             SELECT products.id, name, regular_price, stock_quantity,products.created_at, full_name FROM products
                              LEFT JOIN aggregators ON products.aggregator_id = aggregators.id WHERE admin_id = %s
                              LIMIT %s OFFSET %s
                             """
                cursor.execute(query, (admin_id, limit, offset))

            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f'Error fetching prices: {e}')
        cursor.rollback()
        return None






