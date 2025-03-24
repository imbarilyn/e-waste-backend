from contextlib import closing

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import os
from pathlib import Path


current_directory = Path(__file__).resolve().parent if __file__ in locals() else Path.cwd()
env_file = current_directory / '.env'
load_dotenv(env_file)
localhost= os.getenv('DB_HOST')
user= os.getenv('DB_USER')
password= os.getenv('DB_PASSWORD')
database= os.getenv('DB_DATABASE')
smtp_server= os.getenv('SMTP_SERVER')
email_password= os.getenv('EMAIL_PASSWORD')
sender_email= os.getenv('SENDER_EMAIL')
receiver_email= os.getenv('RECEIVER_EMAIL')
frontend_url=os.getenv('FRONTEND_URL')

# isServer = True
isServer = False

if not isServer:
    DB_CONFIG = {
        "host": localhost,
        "user": user,
        "password": password,
        "database": database,
        "cursorclass": DictCursor
    }
else:
    DB_CONFIG = {
        "host": localhost,
        "user": 'e_waste',
        "password": password,
        "database": database,
        "cursorclass": DictCursor
    }

def get_db():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        yield connection
    finally:
        connection.close()

queries = [
"""
CREATE TABLE IF NOT EXISTS admin(
    id CHAR(36) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number CHAR(10) UNIQUE NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""",
 """
CREATE TABLE IF NOT EXISTS aggregators(
    id CHAR(36) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number CHAR(10) UNIQUE NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dokan_vendor_id VARCHAR(255) NULL DEFAULT  NULL,
    store_name VARCHAR(255) UNIQUE NOT NULL,
    address json NOT NULL,
    categories json NOT NULL,
    admin_id CHAR(36),
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
)

""",
    """
    CREATE TABLE IF NOT EXISTS password_reset(
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    reset_token VARCHAR(255) NOT NULL,
    reset_token_expiry  TIMESTAMP NOT NULL,
    used_reset_token TINYINT(1) DEFAULT 0,
    user_type ENUM('admin', 'aggregator') NOT NULL
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS outbox(
    id CHAR(36) PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    status ENUM('sent', 'pending') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aggregator_id CHAR(36),
    FOREIGN KEY (aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    admin_id CHAR(36),
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS products(
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    regular_price varchar(255) NOT NULL,
    type varchar(255) NOT NULL,
    short_description TEXT,
    stock_quantity varchar(255) NOT NULL,
    weight varchar(255) NOT NULL,
    images JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aggregator_id CHAR(36),
    FOREIGN KEY (aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS secrets(
    id CHAR(36) PRIMARY KEY,
    secret_pass VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aggregator_id CHAR(36),
    FOREIGN KEY (aggregator_id) REFERENCES aggregators(id) ON DELETE CASCADE,
    dokan_vendor_id VARCHAR(255) NOT NULL,
    shop_url VARCHAR(255) NULL
    )
    """,
]

async def create_tables():
        with closing(pymysql.connect(**DB_CONFIG)) as connection:
            with closing(connection.cursor()) as cursor:
                for query in queries:
                   cursor.execute(query)
                connection.commit()


# async def create_tables():
#     with get_db as connection:
#         with connection.cursor() as cursor:
#             cursor.execute(create_table_admin)
#             connection.commit()