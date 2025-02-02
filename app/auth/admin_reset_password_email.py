from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import BackgroundTasks


PORT = 587
SMTP_SERVER = 'smtp.gmail.com'

current_directory = Path(__file__).resolve().parent if '__file__' in locals()else Path.cwd()
env_directory = current_directory / '.env'

# load env variables
load_dotenv(env_directory)

# sender_email = os.getenv('SENDER_EMAIL')
# password_email = os.getenv('EMAIL_PASSWORD')


def send_reset_password_mail(background_tasks: BackgroundTasks, receiver_mail, username, token, email_password, sender_email):
    msg= EmailMessage()
    msg['Subject'] = 'Reset Password'
    msg['From'] = formataddr(('Password Reset', f'{sender_email}'))
    msg['To'] = receiver_mail
    msg.add_alternative(
        f"""\
        <htm>
            <body>
                <p>Hello,<p>
                <span>{username}</span>
                <p>Please click below to reset your password</p>
                <a href="http://localhost:5173/admin/reset-password?token={token}">Reset Password</a>
            </body>
        </htm/>
""",
        subtype='html'
    )

    with smtplib.SMTP(SMTP_SERVER, PORT)as server:
        server.starttls()
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_mail, msg.as_string())

