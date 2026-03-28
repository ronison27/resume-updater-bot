"""
🤖 AI Resume Updater - Telegram Bot
Works on both local and Railway/cloud deployment
"""

import os
import sys
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from pdf_reader import extract_text_from_pdf
from ai_engine import (
    analyze_resume,
    update_resume,
    generate_cover_letter,
    generate_interview_questions
)
from doc_generator import (
    create_resume_pdf,
    create_resume_docx,
    create_cover_letter_pdf
)
from text_cleaner import clean_ai_response

# ============ LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ BOT TOKEN ============
try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# ============ TEMP FOLDER ============
# Use /tmp/ on Railway, local folder on your PC
TEMP_DIR = "/tmp" if os.path.exists("/tmp") else "."

# ============ CONVERSATION STATES ============
UPLOAD_RESUME, PASTE_JD, CHOOSE_ACTION = range(3)


# ============ /start COMMAND ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome_text = """
🤖 *Welcome to AI Resume Updater Bot!*

I can help you tailor your resume for any job!

📌 *What I can do:*
1️⃣ 🔍 Analyze how well your resume matches a JD
2️⃣ 📄 Update your resume to match the JD
3️⃣ 📝 Generate a Cover Letter
4️⃣ 🎯 Generate Interview Questions

📌 *How to use:*
1\\. Send /update to start
2\\. Upload your resume \\(PDF\\)
3\\. Paste the Job Description
4\\. Choose what you want\\!

Let's get started\\! Send /update 🚀
"""
    await update.message.reply_text(
        welcome_text,
        parse_mode='MarkdownV2'
    )


# ============ /help COMMAND ============
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
📌 Available Commands:

/start - Welcome message
/update - Start resume update process
/help - Show this help message
/cancel - Cancel current operation

📌 Steps:
1. Send /update
2. Upload Resume (PDF only)
3. Paste Job Description
4. Choose an action
5. Get results! ✅

Made with ❤️ by Ronison V
"""
    await update.message.reply_text(help_text)


# ============ /update COMMAND ============
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the resume update process"""
    await update.message.reply_text(
        "📎 Step 1/3: Please upload your Resume (PDF file)\n\n"
        "Just drag and drop or attach your PDF here 👇"
    )
    return UPLOAD_RESUME


# ============ RECEIVE RESUME ============
async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded PDF resume"""

    document = update.message.document

    # Check if document exists
    if not document:
        await update.message.reply_text(
            "❌ Please send a PDF file. Try again!"
        )
        return UPLOAD_RESUME

    # Check file type
    file_name = document.file_name or ""
    if not file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Only PDF files are accepted!\n"
            "Please upload a .pdf file."
        )
        return UPLOAD_RESUME

    # Check file size (max 20MB for Telegram)
    file_size = document.file_size or 0
    if file_size > 20 * 1024 * 1024:
        await update.message.reply_text(
            "❌ File is too large! Maximum size is 20MB."
        )
        return UPLOAD_RESUME

    await update.message.reply_text("⏳ Reading your resume... Please wait.")

    try:
        # Download file to temp directory
        user_id = update.effective_user.id
        file_path = os.path.join(TEMP_DIR, f"resume_{user_id}.pdf")

        logger.info(f"Downloading file to: {file_path}")

        # Get file from Telegram
        file = await context.bot.get_file(document.file_id)

        # Download file
        await file.download_to_drive(file_path)

        logger.info(f"File downloaded successfully: {file_path}")

        # Check if file exists after download
        if not os.path.exists(file_path):
            await update.message.reply_text(
                "❌ Failed to download file. Please try again."
            )
            return UPLOAD_RESUME

        # Check file size
        actual_size = os.path.getsize(file_path)
        logger.info(f"File size: {actual_size} bytes")

        if actual_size == 0:
            await update.message.reply_text(
                "❌ Downloaded file is empty. Please try again."
            )
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)
            return UPLOAD_RESUME

        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)

        logger.info(f"Extracted text length: {len(resume_text)}")

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Temp file cleaned up")

        # Check if text extraction was successful
        if not resume_text or resume_text.startswith("❌"):
            await update.message.reply_text(
                "❌ Could not read the PDF.\n\n"
                "Possible reasons:\n"
                "• PDF is image-based (scanned)\n"
                "• PDF is password protected\n"
                "• PDF is corrupted\n\n"
                "Please try a different PDF file."
            )
            return UPLOAD_RESUME

        # Save resume text in user context
        context.user_data['resume_text'] = resume_text

        word_count = len(resume_text.split())

        await update.message.reply_text(
            f"✅ Resume uploaded successfully!\n\n"
            f"📄 Extracted {word_count} words\n\n"
            f"📋 Step 2/3: Now paste the Job Description (JD)\n\n"
            f"Copy the full JD from the job posting and paste it here 👇"
        )
        return PASTE_JD

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")

        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)

        await update.message.reply_text(
            f"❌ Error processing your resume.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again with /update"
        )
        return ConversationHandler.END


# ============ RECEIVE JD ============
async def receive_jd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pasted Job Description"""

    jd_text = update.message.text

    if len(jd_text) < 50:
        await update.message.reply_text(
            "❌ Job description is too short.\n"
            "Please paste the complete JD (at least 50 characters)."
        )
        return PASTE_JD

    # Save JD in user context
    context.user_data['jd_text'] = jd_text

    # Show action buttons
    keyboard = [
        [
            InlineKeyboardButton(
                "🔍 Analyze Match",
                callback_data="analyze"
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Update Resume",
                callback_data="update"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Cover Letter",
                callback_data="cover_letter"
            )
        ],
        [
            InlineKeyboardButton(
                "🎯 Interview Questions",
                callback_data="interview"
            )
        ],
        [
            InlineKeyboardButton(
                "🚀 All of the Above",
                callback_data="all"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ JD received!\n\n"
        "🎯 Step 3/3: What would you like me to do?\n\n"
        "Choose an option below 👇",
        reply_markup=reply_markup
    )
    return CHOOSE_ACTION


# ============ HANDLE BUTTON CLICKS ============
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""

    query = update.callback_query
    await query.answer()

    action = query.data
    resume_text = context.user_data.get('resume_text', '')
    jd_text = context.user_data.get('jd_text', '')
    user_id = update.effective_user.id

    if not resume_text or not jd_text:
        await query.edit_message_text(
            "❌ Something went wrong. Please send /update again."
        )
        return ConversationHandler.END

    # ---- ANALYZE ----
    if action in ["analyze", "all"]:
        await query.edit_message_text("🔍 Analyzing your resume... ⏳")

        try:
            analysis = analyze_resume(resume_text, jd_text)
            analysis = clean_ai_response(analysis)

            if len(analysis) > 4000:
                for i in range(0, len(analysis), 4000):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=analysis[i:i+4000]
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=analysis
                )
        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Analysis failed: {str(e)}"
            )

    # ---- UPDATE RESUME ----
    if action in ["update", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="📄 Updating your resume... ⏳\nThis may take 30-60 seconds."
        )

        try:
            updated = update_resume(resume_text, jd_text)
            updated = clean_ai_response(updated)

            # Send as text
            if len(updated) > 4000:
                for i in range(0, len(updated), 4000):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=updated[i:i+4000]
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=updated
                )

            # Generate & send PDF
            pdf_path = os.path.join(TEMP_DIR, f"Updated_Resume_{user_id}.pdf")
            try:
                result = create_resume_pdf(updated, pdf_path)
                if result and os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=pdf_file,
                            filename="Updated_Resume.pdf",
                            caption="📄 Your updated resume (PDF)"
                        )
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ PDF generation failed: {str(e)}"
                )
            finally:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

            # Generate & send Word
            docx_path = os.path.join(TEMP_DIR, f"Updated_Resume_{user_id}.docx")
            try:
                create_resume_docx(updated, docx_path)
                if os.path.exists(docx_path):
                    with open(docx_path, 'rb') as docx_file:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=docx_file,
                            filename="Updated_Resume.docx",
                            caption="📝 Word format (backup)"
                        )
            except Exception as e:
                logger.error(f"DOCX generation failed: {e}")
            finally:
                if os.path.exists(docx_path):
                    os.remove(docx_path)

        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Resume update failed: {str(e)}"
            )

    # ---- COVER LETTER ----
    if action in ["cover_letter", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="📝 Writing cover letter... ⏳"
        )

        try:
            cover_letter = generate_cover_letter(resume_text, jd_text)
            cover_letter = clean_ai_response(cover_letter)

            await context.bot.send_message(
                chat_id=user_id,
                text=cover_letter
            )

            # Generate & send PDF
            cl_pdf_path = os.path.join(TEMP_DIR, f"Cover_Letter_{user_id}.pdf")
            try:
                result = create_cover_letter_pdf(cover_letter, cl_pdf_path)
                if result and os.path.exists(cl_pdf_path):
                    with open(cl_pdf_path, 'rb') as cl_file:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=cl_file,
                            filename="Cover_Letter.pdf",
                            caption="📝 Your cover letter (PDF)"
                        )
            except Exception as e:
                logger.error(f"Cover letter PDF failed: {e}")
            finally:
                if os.path.exists(cl_pdf_path):
                    os.remove(cl_pdf_path)

        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Cover letter failed: {str(e)}"
            )

    # ---- INTERVIEW QUESTIONS ----
    if action in ["interview", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎯 Generating interview questions... ⏳"
        )

        try:
            questions = generate_interview_questions(jd_text)
            questions = clean_ai_response(questions)

            if len(questions) > 4000:
                for i in range(0, len(questions), 4000):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=questions[i:i+4000]
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=questions
                )
        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Interview questions failed: {str(e)}"
            )

    # ---- DONE MESSAGE ----
    keyboard = [
        [InlineKeyboardButton(
            "🔄 Update Another Resume",
            callback_data="restart"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ All done! Hope this helps! 🎉\n\n"
             "Send /update to process another resume.",
        reply_markup=reply_markup
    )

    return ConversationHandler.END


# ============ CANCEL ============
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "❌ Cancelled. Send /update to start again."
    )
    context.user_data.clear()
    return ConversationHandler.END


# ============ RESTART CALLBACK ============
async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle restart button"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📎 Send /update to start a new resume update!"
    )
    return ConversationHandler.END


# ============ MAIN ============
def main():
    """Start the bot"""
    print("🤖 Bot is starting...")

    # Check token
    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN is empty!")
        print("Set it in Railway environment variables.")
        sys.exit(1)

    print(f"✅ Token loaded: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"📁 Temp directory: {TEMP_DIR}")

    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("update", update_command)
        ],
        states={
            UPLOAD_RESUME: [
                MessageHandler(
                    filters.Document.ALL,
                    receive_resume
                )
            ],
            PASTE_JD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_jd
                )
            ],
            CHOOSE_ACTION: [
                CallbackQueryHandler(handle_action)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_handler(
        CallbackQueryHandler(restart_callback, pattern="restart")
    )

    # Start polling
    print("✅ Bot is running!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
