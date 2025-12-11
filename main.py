from fastapi import FastAPI
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = FastAPI()

class EmailRequest(BaseModel):
    to: str
    subject: str
    text: str = None
    html: str = None

@app.post("/send")
def send_email(req: EmailRequest):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        return {"error": "Missing credentials"}

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = req.to
    msg["Subject"] = req.subject

    # Add text or HTML body
    if req.html:
        msg.attach(MIMEText(req.html, "html"))
    else:
        msg.attach(MIMEText(req.text, "plain"))

    try:
        # Secure SSL connection to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, req.to, msg.as_string())

        return {"success": True}

    except Exception as e:
        return {"error": str(e)}
