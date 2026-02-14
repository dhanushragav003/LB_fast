
import smtplib
from email.message import EmailMessage
from app.core.config import app_config
from typing import Optional
import resend

# def send_email(
#     to: str,
#     subject: str,
#     text: Optional[str] = None,
#     html: Optional[str] = None
# ):
#     try:
#         msg = EmailMessage()
#         print(app_config.EMAIL_FROM)
#         msg["From"] = app_config.EMAIL_FROM
#         msg["To"] = to
#         msg["Subject"] = subject
#         if html:msg.add_alternative(html, subtype="html")
#         if text: msg.set_content(text)

#         with smtplib.SMTP_SSL(
#             app_config.SMTP_HOST,
#             app_config.SMTP_PORT,
#         ) as smtp:
#             smtp.starttls()
#             smtp.login(app_config.SMTP_USER, app_config.SMTP_PASSWORD)
#             smtp.send_message(msg)
#         return True
#     except Exception as e:
#         print(e)
#         raise e

def send_email(
    to: str,
    subject: str,
    text: Optional[str] = None,
    html: Optional[str] = None
):
    try:
        resend.api_key = app_config.RESEND_API_KEY
        r = resend.Emails.send({
        "from": "LearnBite <learnbite@resend.dev>",
        "to": to,
        "subject": subject,
        "html": html
        })
    except Exception as e:
        print(e)
        raise e

