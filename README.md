# FastAPI Email Microservice (EmailJS Integration)

A lightweight, HTTP-based email microservice built with **FastAPI**.

This service sends emails via the [EmailJS](https://www.emailjs.com/) REST API. It is designed to **bypass SMTP port blocks** (common on cloud platforms like Render, AWS EC2, or Google Cloud) by using standard HTTP POST requests (Port 443) instead of SMTP (Ports 25/465/587).

## 🚀 Features

* **Infrastructure Agnostic:** Runs on Docker, Kubernetes, Bare Metal, or any PaaS.
* **No SMTP Required:** Uses HTTP API calls.
* **FastAPI:** High performance and easy-to-read automatic docs.
* **Secure:** Configuration via Environment Variables.

## 📋 Prerequisites

* Python 3.8+
* An [EmailJS](https://www.emailjs.com/) Account (Free tier available).

## 🛠️ Local Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If you don't have a `requirements.txt`, create one with: `fastapi uvicorn requests pydantic`)*

3.  **Run Locally:**
    ```bash
    uvicorn main:app --reload
    ```
    The server will start at `http://127.0.0.1:8000`.

## ⚙️ Configuration (EmailJS)

You must configure your EmailJS dashboard to match the variables expected by the code.

1.  **Create a Service:** Go to **Email Services** in EmailJS and add a service (e.g., Gmail). Copy the **Service ID**.
2.  **Create a Template:** Go to **Email Templates** and create a new template.
    * **Important:** Map these variables in your template design: `{{to_email}}`, `{{subject}}`, `{{message}}`.
    * Copy the **Template ID**.
3.  **Get Credentials:** Go to **Account > API Keys**. Copy your **Public Key** (User ID) and **Private Key** (Access Token).

## 🔐 Environment Variables

The application relies entirely on environment variables. These can be set in a `.env` file (locally) or in your deployment platform's secrets manager.

| Variable | Description |
| :--- | :--- |
| `MAIL_SERVICE_ID` | Your EmailJS Service ID |
| `MAIL_TEMPLATE_ID` | Your EmailJS Template ID |
| `MAIL_USER_ID` | Your EmailJS Public Key |
| `MAIL_PRIVATE_KEY`| Your EmailJS Private Key |
| `MAIL_EMAIL` | The "From" email address context |

## 🌍 Deployment

You can deploy this microservice anywhere Python runs. Choose your preferred method below.

### Option A: Docker (Recommended)

This method works for AWS ECS, DigitalOcean App Platform, Google Cloud Run, or any server with Docker installed.

1.  **Create a `Dockerfile` in your root directory:**
    ```dockerfile
    FROM python:3.9-slim

    WORKDIR /app

    # Install dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy app code
    COPY . .

    # Expose port (default 8000, or use ENV)
    EXPOSE 8000

    # Start command
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

2.  **Build and Run:**
    ```bash
    docker build -t email-service .
    docker run -p 8000:8000 --env-file .env email-service
    ```

### Option B: General PaaS (Render, Railway, Heroku, etc.)

Most Platform-as-a-Service providers follow the same setup:

1.  **Build Command:** `pip install -r requirements.txt`
2.  **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
    * *Note: `$PORT` is usually automatically injected by the cloud provider.*
3.  **Environment Variables:** Copy the values from your `.env` file into the provider's "Settings" or "Environment" tab.

### Option C: Manual/VPS (Ubuntu/Linux)

If deploying to a raw Linux server (EC2, Droplet, Linode):

1.  **Install Python & Pip:**
    ```bash
    sudo apt update && sudo apt install python3-pip python3-venv
    ```
2.  **Setup Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Run with Gunicorn (Production standard):**
    ```bash
    pip install gunicorn
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
    ```

## 🔌 API Reference

### Send Email

**Endpoint:** `POST /`
**Content-Type:** `application/json`

**Payload:**
```json
{
  "to": "recipient@example.com",
  "subject": "System Notification",
  "text": "This is a plain text message.",
  "html": "<strong>This is HTML.</strong>"
}
