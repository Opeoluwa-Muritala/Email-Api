import logging
import os
import smtplib
from email.message import EmailMessage

import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, model_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL") or os.getenv("MAIL_EMAIL")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") or RESEND_FROM_EMAIL
# Legacy EmailJS settings are retained so existing deployments do not break.
MAIL_SERVICE_ID = os.getenv("MAIL_SERVICE_ID")
MAIL_TEMPLATE_ID = os.getenv("MAIL_TEMPLATE_ID")
MAIL_USER_ID = os.getenv("MAIL_USER_ID")
MAIL_PRIVATE_KEY = os.getenv("MAIL_PRIVATE_KEY")

app = FastAPI()


class EmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    text: str | None = Field(default=None, max_length=100_000)
    html: str | None = Field(default=None, max_length=100_000)

    @model_validator(mode="after")
    def require_message(self):
        if not self.text and not self.html:
            raise ValueError("At least one of text or html is required")
        return self


def resend_configured() -> bool:
    return bool(RESEND_API_KEY and RESEND_FROM_EMAIL)


def smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD and SMTP_FROM_EMAIL)


def legacy_emailjs_configured() -> bool:
    return bool(MAIL_SERVICE_ID and MAIL_TEMPLATE_ID and MAIL_USER_ID)


def send_with_resend(req: EmailRequest) -> bool:
    payload = {"from": RESEND_FROM_EMAIL, "to": [str(req.to)], "subject": req.subject}
    if req.text:
        payload["text"] = req.text
    if req.html:
        payload["html"] = req.html
    try:
        response = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.RequestException:
        logger.exception("Resend request failed; trying SMTP fallback")
        return False
    if response.ok:
        return True
    logger.error("Resend rejected email with status %s; trying SMTP fallback", response.status_code)
    return False


def send_with_smtp(req: EmailRequest) -> None:
    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = str(req.to)
    message["Subject"] = req.subject
    message.set_content(req.text or "")
    if req.html:
        message.add_alternative(req.html, subtype="html")
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)


def send_with_legacy_emailjs(req: EmailRequest) -> bool:
    payload = {
        "service_id": MAIL_SERVICE_ID,
        "template_id": MAIL_TEMPLATE_ID,
        "user_id": MAIL_USER_ID,
        "template_params": {
            "email": os.getenv("MAIL_EMAIL"),
            "to_email": str(req.to),
            "subject": req.subject,
            "message": req.html or req.text,
        },
    }
    if MAIL_PRIVATE_KEY:
        payload["accessToken"] = MAIL_PRIVATE_KEY
    try:
        response = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
    except requests.RequestException:
        logger.exception("Legacy EmailJS request failed")
        return False
    return response.ok or response.text == "OK"


@app.post("/", status_code=status.HTTP_202_ACCEPTED)
def send_email(req: EmailRequest):
    if resend_configured() and send_with_resend(req):
        logger.info("Email accepted by Resend")
        return {"success": True, "provider": "resend", "message": "Email accepted"}
    if legacy_emailjs_configured() and send_with_legacy_emailjs(req):
        logger.info("Email accepted by legacy EmailJS provider")
        return {"success": True, "provider": "emailjs", "message": "Email accepted"}
    if smtp_configured():
        try:
            send_with_smtp(req)
            logger.info("Email sent through SMTP fallback")
            return {"success": True, "provider": "smtp", "message": "Email accepted"}
        except (OSError, smtplib.SMTPException):
            logger.exception("SMTP fallback failed")
    if not resend_configured() and not smtp_configured() and not legacy_emailjs_configured():
        logger.error("No email provider is configured")
        raise HTTPException(status_code=503, detail="Email service is not configured")
    raise HTTPException(status_code=502, detail="Email providers unavailable")


@app.get("/health")
def health_check():
    if not resend_configured() and not smtp_configured() and not legacy_emailjs_configured():
        raise HTTPException(status_code=503, detail="Email service is not configured")
    return {"status": "ok"}
