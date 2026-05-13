import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8628273502:AAGttyvbz9KcGQyPq7EWe35TugWSNO9oOL4"

def safe_eval(expr):
    """Safely evaluate a mathematical expression."""
    # Allow only specific characters
    if not re.match(r'^[\d\+\-\*\/\(\)\.\^ ]+$', expr):
        return None
    try:
        # Replace ^ with ** for Python power operator
        expr = expr.replace('^', '**')
        # Use a limited scope for eval
        result = eval(expr, {"__builtins__": None}, {})
        return result
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎉 Welcome from Calculator Bot!\n\n"
        "✅ You can now use all calculator commands in DM.\n"
        "📌 Supported operations:\n"
        "➕ Addition (+)\n"
        "➖ Subtraction (-)\n"
        "✖ Multiplication (*)\n"
        "➗ Division (/)\n"
        "🧮 Parentheses ( )\n"
        "⏫ Exponentiation (^)\n\n"
        "💡 Example: 2+3*5 or (10+2)^2"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = safe_eval(text)
    
    if result is not None:
        # Format result to avoid scientific notation for large numbers if possible
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Copy", callback_data=f"copy_{result}"),
                InlineKeyboardButton("❌ Delete", callback_data="delete")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Result: `{result}`", reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # If it's not a valid math expression, don't respond to avoid spamming
        pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("copy_"):
        # Since Telegram bots cannot directly write to user's clipboard,
        # we provide a message that is easy to copy (monospace) or just acknowledge.
        # Most users know that clicking monospace text copies it in many TG clients.
        await query.message.reply_text("The result is in monospace above. Tap it to copy!")
    elif query.data == "delete":
        await query.message.delete()

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    # Start Flask in a separate thread
    threading.Thread(target=run_flask).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot is starting...")
    application.run_polling()
