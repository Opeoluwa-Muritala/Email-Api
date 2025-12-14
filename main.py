import os
import logging
import requests  # Replaces smtplib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---- CONFIGURATION ---- #
# Setup basic logging to match the target style
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants (Mapped to EmailJS requirements)
# INFO: Get these from your EmailJS Dashboard > Account / Email Services
MAIL_SERVICE_ID = os.getenv('MAIL_SERVICE_ID')    # The ID of the Gmail service you connected
MAIL_TEMPLATE_ID = os.getenv('MAIL_TEMPLATE_ID')  # The ID of the template you created
MAIL_USER_ID = os.getenv('MAIL_USER_ID')          # Your "Public Key"
MAIL_PRIVATE_KEY = os.getenv('MAIL_PRIVATE_KEY')  # Your "Private Key" (Optional, but safer)

app = FastAPI()

class EmailRequest(BaseModel):
    to: str
    subject: str
    text: str = None
    html: str = None

@app.post("/")
def send_email(req: EmailRequest):
    # Validation
    if not MAIL_USER_ID or not MAIL_SERVICE_ID:
        logger.error("Missing email configuration (MAIL_USER_ID / MAIL_SERVICE_ID)")
        raise HTTPException(status_code=500, detail="Server misconfiguration: missing credentials")

    # Prepare Message Content
    # We combine text/html into one 'message' variable for the template
    message_content = req.html if req.html else req.text
    
    # Payload matches EmailJS API structure
    payload = {
        "service_id": MAIL_SERVICE_ID,
        "template_id": MAIL_TEMPLATE_ID,
        "user_id": MAIL_USER_ID,
        "template_params": {
            "email": "muritalaopeoluwa10@gmail.com"
            "to_email": req.to,      
            "subject": req.subject,  
            "message": message_content 
        }
    }

    # Add Private Key for security (if available)
    if MAIL_PRIVATE_KEY:
        payload['accessToken'] = MAIL_PRIVATE_KEY

    try:
        # Send via HTTP POST (Port 443) - This bypasses the Render SMTP block
        response = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        # Check response
        if response.status_code == 200 or response.text == 'OK':
            logger.info(f"Email sent successfully to {req.to}")
            return {"success": True, "message": "Email sent"}
        else:
            logger.error(f"Provider Error: {response.text}")
            raise HTTPException(status_code=500, detail=f"Email Provider Error: {response.text}")

    except Exception as e:
        logger.error(f"Failed to send email via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
