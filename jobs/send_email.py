import smtplib
from email.mime.text import MIMEText
import os

EMAIL = os.getenv("EMAIL_ADD")
PASSWORD = os.getenv("EMAIL_PASS")
::quit

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)