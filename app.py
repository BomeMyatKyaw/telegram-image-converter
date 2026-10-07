import os
import uuid
import requests

from flask import Flask, request, jsonify
from PIL import Image


app = Flask(__name__)

# CONFIG
BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"].rstrip("/")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
)

TELEGRAM_FILE_API = (
    f"https://api.telegram.org/file/bot{BOT_TOKEN}"
)


# Telegram API helper
def telegram(method, data=None, files=None):

    url = f"{TELEGRAM_API}/{method}"

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# Send message
def send_message(chat_id, text, reply_markup=None):

    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return telegram(
        "sendMessage",
        data=data,
    )


# Answer callback
def answer_callback(callback_id):

    return telegram(
        "answerCallbackQuery",
        data={
            "callback_query_id": callback_id
        },
    )


# Edit message
def edit_message(
    chat_id,
    message_id,
    text,
):

    return telegram(
        "editMessageText",
        data={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        },
    )


# Send document
def send_document(
    chat_id,
    file_path,
    filename,
    caption=None,
):

    data = {
        "chat_id": chat_id,
    }

    if caption:
        data["caption"] = caption

    with open(file_path, "rb") as file:

        response = telegram(
            "sendDocument",
            data=data,
            files={
                "document": (
                    filename,
                    file,
                )
            },
        )

    return response


# Get Telegram file
def download_telegram_file(file_id, output_path):

    result = telegram(
        "getFile",
        data={
            "file_id": file_id
        },
    )

    telegram_file_path = result["result"]["file_path"]

    download_url = (
        f"{TELEGRAM_FILE_API}/{telegram_file_path}"
    )

    response = requests.get(
        download_url,
        timeout=60,
    )

    response.raise_for_status()

    with open(output_path, "wb") as file:

        file.write(response.content)


# Set webhook
def setup_webhook():

    webhook = f"{WEBHOOK_URL}/webhook"

    result = telegram(
        "setWebhook",
        data={
            "url": webhook,
            "allowed_updates": [
                "message",
                "callback_query",
            ],
        },
    )

    print("Webhook setup:", result)

    return result


# START COMMAND
def handle_start(message):

    chat_id = message["chat"]["id"]

    send_message(
        chat_id,
        "👋 Welcome to Image Converter Bot!\n\n"
        "Send me an image and I'll convert it for you.",
    )


# IMAGE RECEIVED
def handle_image(message):

    chat_id = message["chat"]["id"]

    file_id = None

    # Photo
    if "photo" in message:

        photo = message["photo"]

        # Highest resolution
        file_id = photo[-1]["file_id"]

    # Document
    elif "document" in message:

        document = message["document"]

        mime_type = document.get(
            "mime_type",
            "",
        )

        if not mime_type.startswith("image/"):

            send_message(
                chat_id,
                "❌ Please send an image file.",
            )

            return

        file_id = document["file_id"]

    else:

        send_message(
            chat_id,
            "❌ Please send an image.",
        )

        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🟢 JPG",
                    "callback_data": "convert_jpg",
                },
                {
                    "text": "🔵 PNG",
                    "callback_data": "convert_png",
                },
            ],
            [
                {
                    "text": "🟣 WEBP",
                    "callback_data": "convert_webp",
                }
            ],
        ]
    }

    send_message(
        chat_id,
        "🖼 Image received!\n\n"
        "Choose the output format:",
        reply_markup=__import__("json").dumps(
            keyboard
        ),
    )

    # Save selected file ID in memory
    # We use chat ID as the key.
    app.config.setdefault(
        "pending_images",
        {},
    )

    app.config["pending_images"][
        str(chat_id)
    ] = file_id


# CONVERT IMAGE
def handle_conversion(callback_query):

    callback_id = callback_query["id"]

    answer_callback(callback_id)

    message = callback_query["message"]

    chat_id = message["chat"]["id"]

    callback_data = callback_query["data"]

    format_name = callback_data.replace(
        "convert_",
        "",
    )

    pending_images = app.config.get(
        "pending_images",
        {},
    )

    file_id = pending_images.get(
        str(chat_id)
    )

    if not file_id:

        send_message(
            chat_id,
            "❌ Image expired.\n"
            "Please send the image again.",
        )

        return

    # Format configuration
    if format_name == "jpg":

        output_format = "JPEG"
        extension = "jpg"

    elif format_name == "png":

        output_format = "PNG"
        extension = "png"

    elif format_name == "webp":

        output_format = "WEBP"
        extension = "webp"

    else:

        send_message(
            chat_id,
            "❌ Unsupported format.",
        )

        return

    edit_message(
        chat_id,
        message["message_id"],
        f"⏳ Converting to {extension.upper()}...",
    )

    unique_id = uuid.uuid4().hex

    input_file = (
        f"/tmp/{unique_id}_input"
    )

    output_file = (
        f"/tmp/{unique_id}.{extension}"
    )

    try:

        # Download original
        download_telegram_file(
            file_id,
            input_file,
        )

        # Open image
        image = Image.open(
            input_file
        )

        # JPG doesn't support transparency
        if output_format == "JPEG":

            if image.mode in (
                "RGBA",
                "LA",
                "P",
            ):

                if image.mode == "P":

                    image = image.convert(
                        "RGBA"
                    )

                background = Image.new(
                    "RGB",
                    image.size,
                    "white",
                )

                if "A" in image.getbands():

                    background.paste(
                        image,
                        mask=image.getchannel(
                            "A"
                        ),
                    )

                else:

                    background.paste(
                        image
                    )

                image = background

            else:

                image = image.convert(
                    "RGB"
                )

        # Save
        if output_format == "JPEG":

            image.save(
                output_file,
                "JPEG",
                quality=95,
            )

        elif output_format == "WEBP":

            image.save(
                output_file,
                "WEBP",
                quality=95,
            )

        else:

            image.save(
                output_file,
                "PNG",
            )

        # Send
        send_document(
            chat_id,
            output_file,
            f"converted.{extension}",
            f"✅ Converted to {extension.upper()}",
        )

        edit_message(
            chat_id,
            message["message_id"],
            "✅ Conversion complete!",
        )

    except Exception as error:

        print(
            "CONVERSION ERROR:",
            repr(error),
        )

        send_message(
            chat_id,
            "❌ Something went wrong while "
            "converting the image.",
        )

    finally:

        if os.path.exists(input_file):

            os.remove(input_file)

        if os.path.exists(output_file):

            os.remove(output_file)

        pending_images.pop(
            str(chat_id),
            None,
        )


# WEBHOOK
@app.post("/webhook")
def webhook():

    try:

        update = request.get_json(
            force=True
        )

        print(
            "Telegram update:",
            update,
        )

        # Message
        if "message" in update:

            message = update["message"]

            # /start
            if (
                "text" in message
                and message["text"].startswith(
                    "/start"
                )
            ):

                handle_start(message)

            # Image
            elif (
                "photo" in message
                or "document" in message
            ):

                handle_image(message)

            else:

                send_message(
                    message["chat"]["id"],
                    "📷 Please send me an image.",
                )

        # Button click
        elif "callback_query" in update:

            handle_conversion(
                update["callback_query"]
            )

        return jsonify(
            {
                "ok": True
            }
        )

    except Exception as error:

        print(
            "WEBHOOK ERROR:",
            repr(error),
        )

        return jsonify(
            {
                "ok": False,
                "error": str(error),
            }
        ), 500


# HEALTH CHECK
@app.get("/")
def home():

    return jsonify(
        {
            "status": "online",
            "service": "Telegram Image Converter",
        }
    )


# WEBHOOK STATUS
@app.get("/webhook-info")
def webhook_info():

    result = telegram(
        "getWebhookInfo"
    )

    return jsonify(result)


# SET WEBHOOK
@app.get("/setup-webhook")
def setup_webhook_route():

    result = setup_webhook()

    return jsonify(result)