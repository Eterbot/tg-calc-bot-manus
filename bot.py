import logging
import os
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyParameters
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
import threading

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
        clean_expr = expr.replace('^', '**')
        # Use a limited scope for eval
        result = eval(clean_expr, {"__builtins__": None}, {})
        return result
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Welcome from Calculator Bot!\n\n"
        "You can now use all calculator commands in DM.\n"
        "Supported operations:\n"
        "Addition (+)\n"
        "Subtraction (-)\n"
        "Multiplication (*)\n"
        "Division (/)\n"
        "Parentheses ( )\n"
        "Exponentiation (^)\n\n"
        "Example: 2+3*5 or (10+2)^2"
    )
    if update.message:
        await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    expr = update.message.text
    result = safe_eval(expr)
    
    if result is not None:
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        
        # Format the display text to show calculation steps
        display_text = f"{expr} = {result}"
        
        # Create keyboard with copy and delete buttons
        # Note: 'copy_text' is a newer feature in some Telegram clients, 
        # but for broad compatibility, we use callback for copy or provide it in monospace
        # The user wants "one-click copy", so we'll use the newer InlineKeyboardButton feature if possible,
        # but the python-telegram-bot version might need specific handling.
        # We will use the copy_text parameter which is supported in Telegram Bot API 7.3+
        
        keyboard = [
            [
                # This button type allows direct copying of the specified text
                InlineKeyboardButton("Copy", copy_text=str(result)),
                InlineKeyboardButton("Delete", callback_data="delete")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(display_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "delete":
        await query.message.delete()

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

async def main():
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot is starting...")
    # Initialize and start the application
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep the bot running
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
