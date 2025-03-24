# from app.auth.auth_aggregator import sender_email
from app.dependencies import SessionDependency
import pymysql
import uuid
from datetime import datetime
from app.database import frontend_url, sender_email, smtp_server, email_password
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

PORT = 587


def get_credentials(aggregator_id: str, db: pymysql.connections.Connection = SessionDependency):
    with db.cursor() as cursor:
        try:
            query = """
             SELECT secrets.secret_pass, secrets.shop_url, aggregators.email, aggregators.first_name, aggregators.admin_id FROM secrets 
                INNER JOIN aggregators ON aggregators.id = secrets.aggregator_id WHERE secrets.aggregator_id = %s
             """
            cursor.execute(query, aggregator_id)
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f'Error fetching secret pass, {e}')
            return None


#
# def get_email_content(dokan_status: bool):
#     if dokan_status:
#         return (
#             head = 'Aggregator Account Activated'
#         body = f"""\
#              <html>
#                  <body>
#                      <p>Hello <strong>{credentials["first_name"]}</strong>,</p>
#                      <p>Your account has been activated successfully.</p>
#
#                      <p>Below are the credentials to your account:</p>
#                      <p><strong>Email:</strong> {credentials["email"]}</p>
#                      <p><strong>Temporary Password:</strong> {credentials["secret_pass"]}</p>
#
#                      <p>Please click the button below to log in and set up your new password:</p>
#                      <a href="{frontend_url}/auth/aggregator-login" class="button">Login to Your Account</a>
#
#                      <p>Thank you.</p>
#                          <p>Best Regards,</p>
#                          <p>Habahaba management</p>
#
#                      <p>&copy; 2025 M-Zawadi Group
#                       | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
#                  </body>
#              </html>
#              """
#         )
#     else:
#         head = 'Aggregator Account Deactivated'
#         body = f"""\
#                               <html>
#                                   <body>
#                                       <p>Hello <strong>{credentials["first_name"]}</strong>,</p>
#                                       <p>It's unfortunate that your account has been deactivated</p>
#
#                                       <p>Please be informed that you can not post any products on the platform until your account is reactivated.</p>
#                                       <p>If you have any questions or concerns, please contact our admin.</p>
#
#                                       # <p>Below are the credentials to your account:</p>
#                                       # <p><strong>Email:</strong> {credentials["email"]}</p>
#                                       # <p><strong>Temporary Password:</strong> {credentials["secret_pass"]}</p>
#
#                                       # <p>Please click the button below to log in and set up your new password:</p>
#                                       # <a href="{frontend_url}/auth/aggregator-login" class="button">Login to Your Account</a>
#
#                                       <p>Thank you.</p>
#                                           <p>Best Regards,</p>
#                                           <p>Habahaba management</p>
#
#                                       <p>&copy; 2025 M-Zawadi Group
#                                        | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
#                                   </body>
#                               </html>
#                               """


def store_aggregator_status_email(
        aggregator_id: str,
        dokan_status: bool,
        db: pymysql.connections.Connection = SessionDependency
):
    print(f"Sending status email {dokan_status}")
    credentials = get_credentials(aggregator_id, db)
    # print(f'Sending status change email {credentials['email']}')

    if credentials:
        email_id = str(uuid.uuid4())
        created_at = datetime.now()
        if dokan_status:
            head = 'Aggregator Account Activated'
            body = f"""\
            <html>
                <body>
                    <p>Hello <strong>{credentials["first_name"]}</strong>,</p>
                    <p>Your account has been activated successfully.</p>
        
                    <p>Below are the credentials to your account:</p>
                    <p><strong>Email:</strong> {credentials["email"]}</p>
                    <p><strong>Temporary Password:</strong> {credentials["secret_pass"]}</p>
                    <p><strong>Link to your shop:</strong>{credentials["shop_url"]}</p>
        
                    <p>Please click the button below to log in and set up your new password:</p>
                    <a href="{frontend_url}/auth/aggregator-login" class="button">Login to Your Account</a>
        
                    <p>Thank you.</p>
                        <p>Best Regards,</p>
                        <p>Habahaba management</p>
        
                    <p>&copy; 2025 M-Zawadi Group
                     | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
                </body>
            </html>
            """
        else:
            head = 'Aggregator Account Deactivated'
            body = f"""\
                      <html>
                          <body>
                              <p>Hello <strong>{credentials["first_name"]}</strong>,</p>
                              <p>It's unfortunate that your account has been deactivated</p>
                              <p>Please be informed that you cannot post any products on the platform until your account is reactivated.</p>                              
                              <p>If you have any questions or concerns, please contact your admin.</p>
                              <p>Thank you.</p>
                                  <p>Best Regards,</p>
                                  <p>Habahaba management</p>

                              <p>&copy; 2025 M-Zawadi Group
                               | Need help? <a href="mailto:support@yourdomain.com">Contact Support</a></p>
                          </body>
                      </html>
                      """
        with db.cursor() as cursor:
            try:
                query = """
                INSERT INTO outbox (id, head, body, created_at, admin_id, aggregator_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (email_id, head, body, created_at, credentials["admin_id"], aggregator_id))
                db.commit()
                is_email_sent = send_email_notification_status(head, body, credentials["email"])
                if is_email_sent:
                    query = """
                    UPDATE outbox SET status = %s WHERE id = %s
                    """
                    cursor.execute(query, ('sent', email_id,))
                    db.commit()
                else:
                    query = """
                    UPDATE outbox SET status = %s WHERE id = %s
                    """
                    cursor.execute(query, ('failed', email_id,))
                return True
            except Exception as e:
                print(f'Error storing email {e}')
                db.rollback()
                return False

    return False


def send_email_notification_status(head: str, body: str, aggregator_email: str):
    try:
        msg = EmailMessage()
        msg['Subject'] = head
        msg['From'] = formataddr(('E-waste Aggregator Status', f'{sender_email}'))
        msg['To'] = aggregator_email
        msg.add_alternative(
            body,
            subtype='html',
        )
        with smtplib.SMTP(smtp_server, PORT) as server:
            server.starttls()
            server.login(sender_email, email_password)
            server.sendmail(sender_email, aggregator_email, msg.as_string())
            server.quit()
            print('Email sent successfully')
            return True
    except Exception as e:
        print(f"Error {e}")
        return False
