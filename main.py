import os
import smtplib
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---- CONFIGURATION ---- #
# Setup basic logging to match the target style
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants from the target snippet
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT', 10))  # seconds
SMTP_USE_STARTTLS = os.getenv('SMTP_USE_STARTTLS', 'true').lower() in ('1', 'true', 'yes')

app = FastAPI()

class EmailRequest(BaseModel):
    to: str
    subject: str
    text: str = None
    html: str = None

@app.post("/")
def send_email(req: EmailRequest):
    # Use the credentials preferred by the target snippet
    sender_email = os.getenv('MAIL_USERNAME')
    sender_password = os.getenv('MAIL_PASSWORD')

    if not sender_email or not sender_password:
        logger.error("Missing email credentials in .env file (MAIL_USERNAME / MAIL_PASSWORD)")
        raise HTTPException(status_code=500, detail="Server misconfiguration: missing credentials")

    # Create Message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = req.to
    msg["Subject"] = req.subject

    # Handle both HTML and Text (Preserving functionality from the first snippet)
    if req.html:
        msg.attach(MIMEText(req.html, "html"))
    elif req.text:
        msg.attach(MIMEText(req.text, "plain"))
    else:
        return {"error": "No message body provided"}

    try:
        # Use context manager and timeout as requested
        # Note: We use standard SMTP here, not SMTP_SSL, to allow for STARTTLS upgrade
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            
            # Optional EHLO/HELO before TLS
            try:
                server.ehlo()
            except Exception:
                pass

            # Logic to handle STARTTLS if configured
            if SMTP_USE_STARTTLS:
                server.starttls()
                try:
                    server.ehlo()
                except Exception:
                    pass

            # Login and Send
            server.login(sender_email, sender_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {req.to}")
        return {"success": True, "message": "Email sent"}

    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        # Return a 500 error so the client knows it failed
        raise HTTPException(status_code=500, detail=str(e))
