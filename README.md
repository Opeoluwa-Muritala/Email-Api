# FastAPI Email API with Resend and SMTP fallback

This service sends email in this order: Resend first, then EmailJS, then SMTP. It is ready for Render and does not require SMTP for the primary path.

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `RESEND_API_KEY` | Recommended | Resend API key |
| `RESEND_FROM_EMAIL` | Recommended | Verified sender, e.g. `Acme <noreply@example.com>` |
| `SMTP_HOST` | Fallback | SMTP server hostname |
| `SMTP_PORT` | Fallback | `587` for STARTTLS or `465` for SSL |
| `SMTP_USERNAME` | Fallback | SMTP username |
| `SMTP_PASSWORD` | Fallback | SMTP password or app password |
| `SMTP_FROM_EMAIL` | Fallback | SMTP sender; defaults to `RESEND_FROM_EMAIL` |
| `MAIL_SERVICE_ID` | Legacy fallback | Existing EmailJS service ID |
| `MAIL_TEMPLATE_ID` | Legacy fallback | Existing EmailJS template ID |
| `MAIL_USER_ID` | Legacy fallback | Existing EmailJS public key |
| `MAIL_PRIVATE_KEY` | Legacy fallback | Existing EmailJS private key |
| `MAIL_EMAIL` | Legacy fallback | Existing sender context |

Configure Resend, EmailJS, SMTP, or any combination. The provider order is Resend → EmailJS → SMTP.

## Local usage

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"to":"recipient@example.com","subject":"Hello","text":"This is a test."}'
```

## Render deployment

The included `render.yaml` defines the Python web service, binds to Render's `$PORT`, configures `/health`, and marks credentials as dashboard secrets.

1. Push the repository to GitHub, GitLab, or Bitbucket.
2. In Render, choose **New → Blueprint** and select the repository.
3. Enter the Resend and SMTP values when prompted.
4. Apply the Blueprint.
