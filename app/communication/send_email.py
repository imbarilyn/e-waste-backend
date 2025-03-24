from app.database import smtp_server, frontend_url, email_password, sender_email
from app.dependencies import SessionDependency
import pymysql
import uuid
from datetime import datetime
from enum import Enum
from email.message import EmailMessage
from email.utils import formataddr
import smtplib



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

    head= 'Aggregator Account Creation'
    body = f"""\
        <html>
            <body>               
            <p>Hello <strong>{aggregator_name}</strong>,</p>
            <p>We’re excited to have you on board! Your account has been successfully created</p>

            <p>Please be patient as the admin activates your account for use. You shall receive another email with your credentials for your account once activated.</p>
            <span>If you are not aware of your account creation, please ignore this email or contact our support team.</span>

            <p>Thank you.</p>
                <p>Best Regards,</p>
                <p>Habahaba management</p>

            <p>&copy; 2025 M-Zawadi Group | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
            </body>
        </html>
        """
    print(f'Receiver email--: {aggregator_email}')
    with db.cursor() as cursor:
        try:
            query = """
            INSERT INTO outbox (id, head, body, created_at, admin_id, aggregator_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (email_id, head, body, created_at, admin_id, aggregator_id))
            db.commit()
            is_email_sent = send_aggregator_creation_email(
                head,
                body,
                aggregator_email
            )
            if is_email_sent:
                query = """
                UPDATE outbox SET status = %s WHERE id = %s
                """
                cursor.execute(query, ('sent', email_id))
                db.commit()
            else:
                query = """
                UPDATE outbox SET status = %s WHERE id = %s
                """
                cursor.execute(query, ('failed', email_id))
                db.commit()
        except Exception as e:
            print(f'Error storing email {e}')
            db.rollback()
            return {
                'message': 'Email not stored',
                'result': 'fail'
            }


def send_aggregator_creation_email(head: str, body: str, aggregator_email: str):
    try:
        msg = EmailMessage()
        msg['Subject'] = head
        msg['From'] = formataddr(('You are an Aggregator', f'{sender_email}'))
        msg['To'] = aggregator_email
        msg.add_alternative(
            body,
            subtype='html'
        )

        with smtplib.SMTP(smtp_server, PORT) as server:
            server.starttls()
            server.login(sender_email, email_password)
            server.sendmail(sender_email, aggregator_email, msg.as_string())
            server.quit()
        print('Email sent')
        return True
    except Exception as e:
        print(f'Error sending email {e}')
        return False

