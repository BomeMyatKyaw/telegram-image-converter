import os
import uuid
import asyncio

from flask import Flask, request
from PIL import Image
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================
# Configuration
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

telegram_app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Image Converter Bot!\n\n"
        "Send me an image and choose the format you want."
    )


# =========================
# Receive image
# =========================

async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message

    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        document = message.document

        if not document.mime_type:
            await message.reply_text(
                "❌ Please send an image."
            )
            return

        if not document.mime_type.startswith("image/"):
            await message.reply_text(
                "❌ That doesn't appear to be an image."
            )
            return

        file_id = document.file_id

    # Save file ID temporarily in user context
    context.user_data["file_id"] = file_id

    keyboard = [
        [
            InlineKeyboardButton("🟢 JPG", callback_data="convert_jpg"),
            InlineKeyboardButton("🔵 PNG", callback_data="convert_png"),
        ],
        [
            InlineKeyboardButton("🟣 WEBP", callback_data="convert_webp"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "🖼 Image received!\n\n"
        "Choose the output format:",
        reply_markup=reply_markup,
    )


# =========================
# Convert image
# =========================

async def convert_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    file_id = context.user_data.get("file_id")

    if not file_id:
        await query.edit_message_text(
            "❌ Image expired. Please send it again."
        )
        return

    format_name = query.data.replace(
        "convert_",
        ""
    )

    extension = format_name

    if format_name == "jpg":
        output_format = "JPEG"
    elif format_name == "png":
        output_format = "PNG"
    elif format_name == "webp":
        output_format = "WEBP"
    else:
        await query.edit_message_text(
            "❌ Unsupported format."
        )
        return

    await query.edit_message_text(
        f"⏳ Converting image to {format_name.upper()}..."
    )

    user_id = query.from_user.id
    unique_id = uuid.uuid4().hex

    input_file = (
        f"/tmp/{user_id}_{unique_id}_input"
    )

    output_file = (
        f"/tmp/{user_id}_{unique_id}.{extension}"
    )

    try:
        # Download Telegram file
        telegram_file = await context.bot.get_file(file_id)

        await telegram_file.download_to_drive(
            input_file
        )

        # Open image
        image = Image.open(input_file)

        # JPG doesn't support transparency
        if output_format == "JPEG":
            if image.mode in (
                "RGBA",
                "LA",
                "P",
            ):
                background = Image.new(
                    "RGB",
                    image.size,
                    "white",
                )

                if image.mode == "P":
                    image = image.convert("RGBA")

                background.paste(
                    image,
                    mask=image.getchannel("A")
                    if "A" in image.getbands()
                    else None,
                )

                image = background

            else:
                image = image.convert("RGB")

        # Convert
        image.save(
            output_file,
            output_format,
            quality=95
            if output_format in ("JPEG", "WEBP")
            else None,
        )

        # Send file
        with open(output_file, "rb") as file:

            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                filename=f"converted.{extension}",
                caption=(
                    f"✅ Converted to "
                    f"{format_name.upper()}"
                ),
            )

        await query.edit_message_text(
            "✅ Conversion complete!"
        )

    except Exception as error:

        print(
            f"Conversion error: {error}"
        )

        await query.edit_message_text(
            "❌ Something went wrong while "
            "converting the image."
        )

    finally:

        # Delete temporary files
        if os.path.exists(input_file):
            os.remove(input_file)

        if os.path.exists(output_file):
            os.remove(output_file)

        context.user_data.pop(
            "file_id",
            None,
        )


# =========================
# Telegram webhook
# =========================

@app.post("/webhook")
async def webhook():

    data = request.get_json(
        force=True
    )

    update = Update.de_json(
        data,
        telegram_app.bot,
    )

    await telegram_app.process_update(
        update
    )

    return "OK", 200


# =========================
# Health check
# =========================

@app.get("/")
def home():

    return {
        "status": "online",
        "service": "Telegram Image Converter",
    }


# =========================
# Start bot
# =========================

async def setup_bot():

    await telegram_app.initialize()

    await telegram_app.start()

    webhook_url = (
        f"{WEBHOOK_URL}/webhook"
    )

    await telegram_app.bot.set_webhook(
        url=webhook_url
    )

    print(
        f"Webhook set: {webhook_url}"
    )


# =========================
# Main
# =========================

if __name__ == "__main__":

    asyncio.run(setup_bot())

    app.run(
        host="0.0.0.0",
        port=PORT,
    )