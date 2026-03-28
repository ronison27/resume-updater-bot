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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
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
# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation States
UPLOAD_RESUME, PASTE_JD, CHOOSE_ACTION = range(3)


# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome_text = """
🤖 **Welcome to AI Resume Updater Bot!**

I can help you tailor your resume for any job!

📌 **What I can do:**
1️⃣ 🔍 Analyze how well your resume matches a JD
2️⃣ 📄 Update your resume to match the JD
3️⃣ 📝 Generate a Cover Letter
4️⃣ 🎯 Generate Interview Questions

📌 **How to use:**
1. Send /update to start
2. Upload your resume (PDF)
3. Paste the Job Description
4. Choose what you want!

Let's get started! Send /update 🚀
"""
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
📌 **Available Commands:**

/start - Welcome message
/update - Start resume update process
/help - Show this help message
/cancel - Cancel current operation

📌 **Steps:**
1. Send /update
2. Upload Resume (PDF only)
3. Paste Job Description
4. Choose an action
5. Get results! ✅

Made with ❤️ by Ronison V
"""
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )


# ============ CONVERSATION HANDLERS ============

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the resume update process"""
    await update.message.reply_text(
        "📎 **Step 1/3:** Please upload your **Resume (PDF file)**\n\n"
        "Just drag and drop or attach your PDF here 👇",
        parse_mode='Markdown'
    )
    return UPLOAD_RESUME


async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded PDF resume"""

    # Check if document is PDF
    document = update.message.document

    if not document:
        await update.message.reply_text(
            "❌ Please send a **PDF file**. Try again!",
            parse_mode='Markdown'
        )
        return UPLOAD_RESUME

    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Only **PDF files** are accepted. Please upload a PDF!",
            parse_mode='Markdown'
        )
        return UPLOAD_RESUME

    await update.message.reply_text("⏳ Reading your resume...")

    # Download the file
    file = await context.bot.get_file(document.file_id)
    file_path = f"temp_{update.effective_user.id}.pdf"
    await file.download_to_drive(file_path)

    # Extract text
    resume_text = extract_text_from_pdf(file_path)

    # Clean up temp file
    if os.path.exists(file_path):
        os.remove(file_path)

    if not resume_text or "Error" in resume_text:
        await update.message.reply_text(
            "❌ Could not read the PDF. Please try another file.",
        )
        return UPLOAD_RESUME

    # Save resume text in user context
    context.user_data['resume_text'] = resume_text

    await update.message.reply_text(
        f"✅ **Resume uploaded successfully!**\n\n"
        f"📄 Extracted {len(resume_text.split())} words\n\n"
        f"📋 **Step 2/3:** Now paste the **Job Description (JD)**\n\n"
        f"Copy the full JD from the job posting and paste it here 👇",
        parse_mode='Markdown'
    )
    return PASTE_JD


async def receive_jd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pasted Job Description"""

    jd_text = update.message.text

    if len(jd_text) < 50:
        await update.message.reply_text(
            "❌ Job description is too short. "
            "Please paste the **complete JD**.",
            parse_mode='Markdown'
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
        "✅ **JD received!**\n\n"
        "🎯 **Step 3/3:** What would you like me to do?\n\n"
        "Choose an option below 👇",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CHOOSE_ACTION

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
            "❌ Something went wrong. Please /update again."
        )
        return ConversationHandler.END

    # ---- ANALYZE ----
    if action in ["analyze", "all"]:
        await query.edit_message_text("🔍 Analyzing your resume... ⏳")

        analysis = analyze_resume(resume_text, jd_text)

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

    # ---- UPDATE RESUME ----
    if action in ["update", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="📄 Updating your resume... ⏳"
        )

        updated = update_resume(resume_text, jd_text)
        updated = clean_ai_response(updated)
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
        pdf_path = f"Updated_Resume_{user_id}.pdf"
        result = create_resume_pdf(updated, pdf_path)

        if result:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(pdf_path, 'rb'),
                filename="Updated_Resume.pdf",
                caption="📄 Your updated resume (PDF)"
            )

        # Also send Word as backup
        docx_path = f"Updated_Resume_{user_id}.docx"
        create_resume_docx(updated, docx_path)

        await context.bot.send_document(
            chat_id=user_id,
            document=open(docx_path, 'rb'),
            filename="Updated_Resume.docx",
            caption="📝 Word format (backup)"
        )

        # Clean up files
        for f in [pdf_path, docx_path]:
            if os.path.exists(f):
                os.remove(f)

    # ---- COVER LETTER ----
    if action in ["cover_letter", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="📝 Writing cover letter... ⏳"
        )

        cover_letter = generate_cover_letter(resume_text, jd_text)

        await context.bot.send_message(
            chat_id=user_id,
            text=cover_letter
        )

        cl_pdf_path = f"Cover_Letter_{user_id}.pdf"
        result = create_cover_letter_pdf(cover_letter, cl_pdf_path)

        if result:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(cl_pdf_path, 'rb'),
                filename="Cover_Letter.pdf",
                caption="📝 Your cover letter (PDF)"
            )

        if os.path.exists(cl_pdf_path):
            os.remove(cl_pdf_path)

    # ---- INTERVIEW QUESTIONS ----
    if action in ["interview", "all"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎯 Generating interview questions... ⏳"
        )

        questions = generate_interview_questions(jd_text)

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
        text="✅ **All done!** Hope this helps! 🎉\n\n"
             "Send /update to process another resume.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "❌ Operation cancelled. Send /update to start again.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle restart button click"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 Restarting...")
    await update_command(query, context)

try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# ============ MAIN ============
def main():
    """Start the bot"""
    print("🤖 Bot is starting...")
   # Check if token exists
    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN is empty!")
        print("Please set it in Railway environment variables.")
        sys.exit(1)

    print(f"✅ Token loaded: {TELEGRAM_BOT_TOKEN[:10]}...")

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
