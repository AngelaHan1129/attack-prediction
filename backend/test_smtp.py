import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "tinaowo111@gmail.com"
SMTP_PASSWORD = "qyxrncfqhgmijppz"

msg = EmailMessage()
msg["Subject"] = "SMTP 測試"
msg["From"] = SMTP_USERNAME
msg["To"] = SMTP_USERNAME
msg.set_content("這是一封測試信")

with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.send_message(msg)