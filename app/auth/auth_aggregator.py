import random
import uuid
from jwt import InvalidTokenError
import pymysql
from sqlmodel import SQLModel
from fastapi import APIRouter, Depends, HTTPException, status, Form, BackgroundTasks
from pathlib import Path
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
import jwt
from secrets import token_urlsafe
import os

from ..communication.send_email import store_email
from ..dependencies import SessionDependency
from app.auth.auth_admin import get_active_admin
from app.auth.auth_admin import TokenData




router = APIRouter(
    prefix="/auth/aggregator",
    tags=['auth-aggregator']
)


current_dir = Path(__file__).resolve().parent if __file__ in locals() else Path.cwd()
env_directory = current_dir / '.env'
load_dotenv(env_directory)
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/aggregator/token')

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITH= os.getenv('ALGORITHM')
sender_email = os.getenv('SENDER_EMAIL')
email_password = os.getenv('EMAIL_PASSWORD')
ACCESS_TOKEN_EXPIRE = 7




class Token(SQLModel):
    access_token: str
    token_type: str

class ForgottenPassword(SQLModel):
    email: str


def verify_password(plain_password: str, hash_password: str):
    return bcrypt_context.verify(plain_password, hash_password)



def get_hashed_password(password: str):
    return bcrypt_context.hash(password)


def validate_reset_password(token: str, db: pymysql.connections.Connection, now:datetime):
    with db.cursor() as cursor:
        query = """
        SELECT * FROM e_waste.password_reset WHERE reset_token = %s
        AND used_reset_token = %s
        AND reset_token_expiry > %s
        """
        cursor.execute(query, (token, 0, now))
        valid_token = cursor.fetchone()
        if valid_token:
            return valid_token
        return False


def get_user_by_email(db: pymysql.connections.Connection, email: str):
    with db.cursor() as cursor:
        query = """
        SELECT * FROM e_waste.aggregators WHERE email = %s
        """
        cursor.execute(query, email)
        admin = cursor.fetchone()
        if admin:
            return admin
        return None

def get_user(phone_number: str, email: str, db: pymysql.connections.Connection):
    with db.cursor() as cursor:
        query = "SELECT * FROM e_waste.aggregators WHERE phone_number = %s OR  email = %s"
        cursor.execute(query, (phone_number, email))
        user = cursor.fetchone()
        if user:
            return user
        return None

def get_active_aggregator(token: str = Depends(oauth2_scheme) , db: pymysql.connections.Connection = SessionDependency):
    credential_exception = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITH)
        full_name: str = payload.get('sub')
        user_id: int = payload.get('user_id')
        exp: str = payload.get('exp')
        email: str = payload.get('email')
        if full_name is None or user_id is None:
            raise credential_exception
        return {'full_name': full_name, 'user_id': user_id, 'exp': exp, 'email': email}
    except InvalidTokenError:
        raise credential_exception

def authenticate_user(phone_number: str, password: str, db: pymysql.connections.Connection):
    with db.cursor() as cursor:
        query = """
        SELECT * FROM e_waste.aggregators WHERE phone_number = %s
        """
        cursor.execute(query, phone_number)
        aggregator = cursor.fetchone()
        if not aggregator:
            return  False
        if not verify_password(password, aggregator['hash_password']):
            return  False
        return aggregator

def create_reset_token(aggregator_id: str , db: pymysql.connections.Connection):
    EXPIRY_DURATION = 24
    reset_token = token_urlsafe(32)
    reset_token_expiry = datetime.now() + timedelta(hours=EXPIRY_DURATION)
    reset_password_id = uuid.uuid4()
    with db.cursor() as cursor:
        try:
            query = """
            INSERT INTO e_waste.password_reset(id, user_id, reset_token, reset_token_expiry, user_type)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (reset_password_id, aggregator_id, reset_token, reset_token_expiry, 'aggregator'))
            db.commit()
            select_query = """
            SELECT * FROM e_waste.password_reset WHERE id = LAST_INSERT_ID()
            """
            cursor.execute(select_query)
            return cursor.fetchone()
        except Exception as e:
            print(e)
            return None

@router.post('/forgot-password')
def forgot_password(forgot_password_request: ForgottenPassword, background_tasks: BackgroundTasks, db: pymysql.connections.Connection = SessionDependency):
    user = get_user_by_email(db, forgot_password_request.email)
    if not user:
        return {
            'message': 'User not found',
            'result': 'fail'
        }
    password_reset = create_reset_token(user['id'], db)
    print(f'Password reset {password_reset}')
    print(f"User!!! {user}")
    if password_reset:
        # send_reset_password_mail(background_tasks, user['email'], user['full_name'], password_reset['reset_token'], email_password, sender_email)
        return  {
            'message': 'Reset token sent to email, kindly reset password',
            'result': 'success',

        }
    return {
        'message': 'Something went wrong, please try again',
        'result': 'fail',
    }


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expires_in = datetime.now(timezone.utc) + expires_delta
    else:
        expires_in = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expires_in})
    jwt_encoded = jwt.encode(to_encode, SECRET_KEY, ALGORITH)
    return jwt_encoded

class OAuth2PasswordRequestFormCustom(OAuth2PasswordRequestForm):
    def __init__(self,
                phone_number: str = Form(...),
                 password: str = Form(...),
                ):
            super().__init__(username=phone_number, password=password)

def get_current_active_aggregator(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITH)
        full_name: str = payload.get('sub')
        user_id: int = payload.get('user_id')
        exp: str = payload.get('exp')
        email: str = payload.get('email')
        if full_name is None or user_id is None:
            raise credential_exception
        return {'full_name': full_name, 'user_id': user_id, 'exp': exp, 'email': email}
    except InvalidTokenError:
        raise credential_exception


    # create admin
@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestFormCustom = Depends(), db: pymysql.connections.Connection = SessionDependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise  HTTPException (
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail='Wrong credentials',
            headers={"WWW-authorization": 'Bearer'}
        )

    access_token_expires = timedelta(days = ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(data={"sub": user['full_name'], "user_id": user['id'], "email": user['email']}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type='bearer')


@router.post("/create")
async def create_user(
        full_name: str = Form(...),
        email: str = Form(...),
        phone_number: str = Form(...),
        location: str = Form(...),
        admin_id: str = Form(...),
        db: pymysql.connections.Connection = SessionDependency, admin: dict = Depends(get_active_admin)):
    user_in_db = get_user(phone_number, email, db)
    if user_in_db:
        return {
            'message': 'Phone number or email already taken',
            'result': 'fail'
        }
    else:
        password = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        aggregator_id = str(uuid.uuid4())
        hash_password = get_hashed_password(password)
        with db.cursor() as cursor:
            try:
                new_user = """
                INSERT INTO e_waste.aggregators (id, full_name, email, phone_number, location, hash_password, created_at, admin_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(new_user, (
                    aggregator_id,
                    full_name,
                    email,
                    phone_number,
                    location,
                    hash_password,
                    datetime.now(),
                    admin_id,

                )
                )
                store_email(
                    password,
                    admin_id,
                    aggregator_id,
                    full_name,
                    email,
                    db
                )
                db.commit()
                return {
                    "message": "Aggregator created successfully",
                    "result": "success",
                }
            except Exception as e:
                print(f'Create aggregator exception--- f{e}')
                return {
                    'message': 'Something went wrong, please try again',
                    'result': 'fail'
                }


#
@router.put('/reset-password')
def reset_password(
        password: str = Form(...),
        confirm_password: str = Form(...),
        token: str = Form(...),
        db:pymysql.connections.Connection = SessionDependency):

    now = datetime.now()
    everything_valid = validate_reset_password(token, db, now)
    print(f"Everything valid {everything_valid}")
    if everything_valid:
        match_password = confirm_password == password
        if not match_password:
            return {
                'message': 'Passwords do not match',
                'result': 'fail'
            }
        hashed_new_password = get_hashed_password(password)
        with db.cursor() as cursor:
            try:
                query_aggregator ="""
                UPDATE e_waste.admin SET
                hash_password = %s
                WHERE id = %s
                """
                cursor.execute(query_aggregator, (hashed_new_password, everything_valid['user_id']))

                query_password_reset = """
                UPDATE e_waste.password_reset SET 
                used_reset_token = %s
                WHERE reset_token = %s
                """
                cursor.execute(query_password_reset, (1, token))
                db.commit()
                return {
                    'message': 'Password reset successfully',
                    'result': 'success',
                }
            except Exception as e:
                print(e)
                return {
                    'message': 'Something went wrong, please try again',
                    'result': 'fail'
                }
    return{
        'message': 'Invalid or expired token',
        'result': 'fail'
    }