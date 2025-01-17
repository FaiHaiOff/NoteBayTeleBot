import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Replace with your tokens and IDs
TELEGRAM_TOKEN = "7704908746:AAG0it3ysua-WfMsoRe33T0SClPe99al-DM"  # Replace with your Telegram bot token
SERVICE_ACCOUNT_FILE = "google drive key.json"  # Replace with your service account JSON file path
DRIVE_FOLDER_ID = "1ZVNRIa3QI7evCem6cl1SOcFgI9S9"  # Replace with the Google Drive folder ID

# Google Drive API setup
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
drive_service = build("drive", "v3", credentials=credentials)

# Command handler: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to the Study Material Bot! 📚\n"
        "You can:\n"
        "- Send a keyword to search for study materials\n"
        "- Upload a PDF document to share with others"
    )

# Message handler: Search for files
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle keyword searches."""
    query = update.message.text
    files = search_files(query)
    if not files:
        await update.message.reply_text("No files found for your query. Try another keyword!")
    else:
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
            await update.message.reply_text(f"📄 {file_name}\n🔗 {download_url}")

# Document handler: Upload files
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF document uploads."""
    document = update.message.document
    if document.mime_type == "application/pdf":
        file = await context.bot.get_file(document.file_id)
        file_path = f"downloads/{document.file_name}"
        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(file_path)
        
        # Upload to Google Drive
        upload_to_drive(file_path, document.file_name)
        await update.message.reply_text(f"File '{document.file_name}' uploaded successfully! ✅")
    else:
        await update.message.reply_text("Please send only PDF files.")

# Helper function: Search files in Google Drive
def search_files(query):
    """Search for files in Google Drive by keyword."""
    try:
        results = (
            drive_service.files()
            .list(
                q=f"name contains '{query}' and '{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf'",
                fields="files(id, name)",
            )
            .execute()
        )
        return results.get("files", [])
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return []

# Helper function: Upload files to Google Drive
def upload_to_drive(file_path, file_name):
    """Upload a file to Google Drive."""
    try:
        file_metadata = {"name": file_name, "parents": [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(file_path, mimetype="application/pdf")
        drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        logger.info(f"Uploaded file: {file_name}")
    except Exception as e:
        logger.error(f"Error uploading file: {e}")

# Main function
def main():
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
