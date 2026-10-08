# 🖼️ Telegram Image Converter Bot

A simple Telegram bot that converts images between **JPG, PNG, and WEBP** formats directly inside Telegram.

The bot is built with **Python, Flask, Pillow, and the Telegram Bot API**, and is designed to run on **Render** using a webhook.

## ✨ Features

- 🖼️ Convert images directly from Telegram
- 🟢 Convert to JPG
- 🔵 Convert to PNG
- 🟣 Convert to WEBP
- 📷 Supports normal Telegram photos
- 📁 Supports images sent as Telegram documents
- 🖼️ Preserves image quality during conversion
- 🔄 Uses Telegram Webhooks
- ☁️ Ready for Render deployment
- 🧹 Automatically removes temporary files after conversion

## 🛠️ Tech Stack

- **Python**
- **Flask** — Web server and webhook handler
- **Pillow** — Image processing and conversion
- **Requests** — Telegram Bot API requests
- **Gunicorn** — Production WSGI server
- **Render** — Cloud deployment
- **Telegram Bot API**

## 📁 Project Structure

```text
telegram-image-converter/
│
├── app.py
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

### `app.py`

Main application containing:

- Telegram Bot API integration
- Webhook handling
- Image downloading
- Image conversion
- Converted file uploading
- Health check endpoint
- Webhook management

### `requirements.txt`

Contains the Python dependencies required by the bot.

### `render.yaml`

Contains the Render deployment configuration.

---

# 🤖 How It Works

The bot uses the following workflow:

```text
User sends image
       │
       ▼
Telegram Bot
       │
       ▼
Flask Webhook
       │
       ▼
Image received
       │
       ▼
Choose output format
       │
       ├── JPG
       ├── PNG
       └── WEBP
       │
       ▼
Download image from Telegram
       │
       ▼
Pillow converts image
       │
       ▼
Send converted image
       │
       ▼
Temporary files deleted
```

## 💬 Bot Usage

Start the bot with:

```text
/start
```

The bot will respond with:

```text
👋 Welcome to Image Converter Bot!

Send me an image and I'll convert it for you.
```

### 1. Send an Image

Send an image to the bot.

The bot will show:

```text
🖼 Image received!

Choose the output format:
```

With these options:

```text
🟢 JPG
🔵 PNG
🟣 WEBP
```

### 2. Choose the Format

Select the desired format.

The bot will convert the image and send the converted file back to you.

---

# 🚀 Run Locally

## Requirements

Make sure you have:

- Python 3.10+
- A Telegram Bot
- A Telegram Bot Token

Create a bot using **@BotFather** on Telegram and copy the bot token.

## 1. Clone the Repository

```bash
git clone https://github.com/BomeMyatKyaw/telegram-image-converter.git

cd telegram-image-converter
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Set the following environment variables:

```text
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-public-domain.com
```

### `BOT_TOKEN`

Your Telegram bot token from BotFather.

Example:

```text
BOT_TOKEN=123456789:ABCxxxxxxxxxxxxxxxxxxxx
```

### `WEBHOOK_URL`

The public HTTPS URL where your Flask application is running.

Example:

```text
WEBHOOK_URL=https://telegram-image-converter.onrender.com
```

Do **not** include `/webhook` at the end.

Correct:

```text
WEBHOOK_URL=https://your-app.onrender.com
```

Incorrect:

```text
WEBHOOK_URL=https://your-app.onrender.com/webhook
```

The application automatically adds:

```text
/webhook
```

---

# ▶️ Run the Application

For local development:

```bash
python app.py
```

Or with Gunicorn:

```bash
gunicorn app:app
```

The application provides:

```text
GET /
```

for a health check.

Example response:

```json
{
  "status": "online",
  "service": "Telegram Image Converter"
}
```

---

# ☁️ Deploy to Render

This project includes a `render.yaml` file, so it can be deployed directly to Render.

## 1. Push the Repository to GitHub

Make sure the project is available on GitHub.

## 2. Create a Render Web Service

Open Render and create a new Web Service from the GitHub repository.

Render will detect the Python project configuration.

The project uses:

```yaml
runtime: python
```

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app
```

## 3. Add Environment Variables

In Render, add:

```text
BOT_TOKEN
```

and:

```text
WEBHOOK_URL
```

For example:

```text
BOT_TOKEN=your_telegram_bot_token
```

```text
WEBHOOK_URL=https://telegram-image-converter.onrender.com
```

Keep your `BOT_TOKEN` private.

**Never commit your Telegram bot token to GitHub.**

## 4. Deploy

After deployment, open:

```text
https://your-app.onrender.com/
```

You should receive:

```json
{
  "status": "online",
  "service": "Telegram Image Converter"
}
```

---

# 🔗 Configure the Telegram Webhook

After your Render service is running, open:

```text
https://your-app.onrender.com/setup-webhook
```

This endpoint tells Telegram to send bot updates to:

```text
https://your-app.onrender.com/webhook
```

You can check the webhook status using:

```text
https://your-app.onrender.com/webhook-info
```

Telegram should return information about the configured webhook.

---

# 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot API token |
| `WEBHOOK_URL` | ✅ | Public HTTPS URL of the deployed application |

Example:

```env
BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://your-app.onrender.com
```

---

# 📷 Supported Formats

### Input

The bot can receive images through:

- Telegram photos
- Telegram image documents

### Output

| Format | Extension |
|---|---|
| JPEG | `.jpg` |
| PNG | `.png` |
| WEBP | `.webp` |

---

# 🖼️ JPEG Transparency

JPEG does not support transparency.

When converting a transparent image to JPG, the bot creates a **white background** before saving the JPEG.

For example:

```text
PNG with transparency
        ↓
Transparent areas
        ↓
White background
        ↓
JPG
```

---

# 🧹 Temporary Files

Images are temporarily stored in `/tmp` while they are being processed.

After conversion, the bot automatically removes:

```text
input file
output file
```

This keeps the server clean and reduces unnecessary storage usage.

---

# 🔒 Security

Keep your Telegram bot token private.

Never put it directly inside:

```python
BOT_TOKEN = "your-token"
```

Instead, this project uses an environment variable:

```python
BOT_TOKEN = os.environ["BOT_TOKEN"]
```

If your bot token is accidentally exposed, regenerate it using BotFather.

---

# 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/webhook` | Telegram webhook |
| `GET` | `/webhook-info` | Check Telegram webhook |
| `GET` | `/setup-webhook` | Configure Telegram webhook |

---

# 🧪 Testing

After deployment:

1. Open your Telegram bot.
2. Send `/start`.
3. Send an image.
4. Select `JPG`, `PNG`, or `WEBP`.
5. Wait for the conversion.
6. The converted image will be sent back.

If the bot does not respond, check:

```text
/
```

to verify the server is online.

Then check:

```text
/webhook-info
```

to verify that Telegram has the correct webhook.

---

# 🐛 Troubleshooting

### Bot does not respond

Check:

```text
https://your-app.onrender.com/
```

If the service is online, check:

```text
https://your-app.onrender.com/webhook-info
```

### Webhook is not configured

Open:

```text
https://your-app.onrender.com/setup-webhook
```

### Bot says the image expired

The selected image is temporarily stored in memory. Send the image again and choose the output format.

### Image conversion fails

Check the Render application logs for:

```text
CONVERSION ERROR
```

or:

```text
WEBHOOK ERROR
```

---

# 📜 License

This project is open source. See the repository for license information.

---

# 👨‍💻 Author

**Bome Myat Kyaw**

GitHub:

https://github.com/BomeMyatKyaw

Repository:

https://github.com/BomeMyatKyaw/telegram-image-converter
