from app.auth.admin_reset_password_email import SMTP_SERVER
from app.database import email_password, smtp_server, frontend_url, email_password, sender_email, receiver_email
from app.dependencies import SessionDependency
import pymysql
import uuid
from datetime import datetime
from enum import Enum
from email.message import EmailMessage
from email.utils import formataddr
import smtplib


class Status(str, Enum):
    pending = 'pending'
    sent = 'sent'
    failed = 'failed'


PORT = 587


def store_email(
        password: str,
        admin_id: str,
        aggregator_id: str,
        aggregator_name: str,
        aggregator_email: str,
        db: pymysql.connections.Connection = SessionDependency
):
    email_id = str(uuid.uuid4())
    created_at = datetime.now()

    subject = 'Aggregator Account Creation'
    body = f"""\
        <html>
            <body>               
            <p>Hello <strong>{aggregator_name}</strong>,</p>
            <p>We’re excited to have you on board! Your account has been successfully created. Below are your login details:</p>

            <p><strong>Email:</strong> {aggregator_email}</p>
            <p><strong>Temporary Password:</strong> {password}</p>

            <p>Please click the button below to log in and set up your new password:</p>
            <a href="{frontend_url}/auth/aggregator-login" class="button">Login to Your Account</a>
            <p>If you are not aware of your account creation, please ignore this email or contact our support team.</p>



            <p>Thank you.</p>
                <p>Best Regards,</p>
                <p>Habahaba management</p>




            <p>&copy; 2025 [Your Company Name] | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
            </body>
        </html>
        """
    with db.cursor() as cursor:
        try:
            query = """
            INSERT INTO outbox (id, subject, body, status, created_at, admin_id, aggregator_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (email_id, subject, body, Status.pending.value, created_at, admin_id, aggregator_id))
            db.commit()
            send_aggregator_creation_email(
                db,
                email_id,
                subject,
                body,
                aggregator_email
            )
        except Exception as e:
            print(e)
            db.rollback()
            return {
                'message': 'Email not stored',
                'result': 'fail'
            }


def send_aggregator_creation_email(db: pymysql.connections.Connection, email_id: str, subject: str, body: str,
                                   aggregator_email: str):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr(('You are an Aggregator', f'{sender_email}'))
        msg['To'] = aggregator_email
        msg.add_alternative(
            body,
            subject='html'
        )

        with smtplib.SMTP(SMTP_SERVER, PORT) as server:
            server.starttls()
            server.login(sender_email, email_password)
            server.sendmail(sender_email, aggregator_email, msg.as_string())
            server.quit()
            with db.cursor() as cursor:
                try:
                    query = """
                    UPDATE outbox SET status = %s WHERE id = %s
                    """
                    cursor.execute(query, (Status.sent.value, email_id))
                    db.commit()
                except Exception as e:
                    print(f'Error updating outbox {e}')
                    db.rollback()
    except Exception as e:
        with db.cursor() as cursor:
            try:
                query = """
                           UPDATE outbox SET status = %s WHERE id = %s
                           """
                cursor.execute(query, (Status.failed.value, email_id))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f'Error updating outbox {e}')




