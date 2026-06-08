import logging
import os
import re
import asyncio
import threading
import uuid
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
TOKEN = os.getenv("BOT_TOKEN", "8223310359:AAHBf7xXUCvd5PX-ojobMKCIVfGE2CwQEZ0")

def format_number(number):
    """Formats a number with thousand separators."""
    if isinstance(number, (int, float)):
        if isinstance(number, float) and number.is_integer():
            number = int(number)
        return "{:,}".format(number)
    return str(number)

def safe_eval(expr):
    """Safely evaluate a mathematical expression."""
    # Allow only specific characters (including ÷ and ×)
    if not re.match(r'^[\d\+\-\*\/\(\)\.\^ ÷×]+$', expr):
        return None
    try:
        # Replace mathematical symbols with Python operators
        clean_expr = expr.replace('^', '**').replace('×', '*').replace('÷', '/')
        # Use a limited scope for eval
        result = eval(clean_expr, {"__builtins__": None}, {})
        return result
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎉 Welcome from Mixx's Calculator Bot!\n"
        "✅ You can now use all calculator commands in DM.\n"
        "📌 Supported operations:\n"
        "➕ Addition (+)\n"
        "➖ Subtraction (-)\n"
        "✖️ Multiplication (*)\n"
        "➗ Division (/)\n"
        "🔢 Parentheses ( )\n"
        "⬆️ Exponentiation (^)\n"
        "💡 Example: 2+3*5 or (10+2)^2"
    )
    if update.message:
        await update.message.reply_text(welcome_text)
    elif update.business_message:
        await update.business_message.reply_text(welcome_text)

async def handle_calculation(expr):
    """Common logic for calculation and formatting."""
    # Check if it looks like a math expression (contains at least one digit)
    if not any(char.isdigit() for char in expr):
        return None, None
        
    result = safe_eval(expr)
    if result is not None:
        formatted_result = format_number(result)
        display_text = f"<code>{expr} = {formatted_result}</code>"
        return result, display_text
    return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support both regular messages and business messages
    msg = update.message or update.business_message
    if not msg or not msg.text:
        return
        
    expr = msg.text.strip()
    result, display_text = await handle_calculation(expr)
    
    if result is not None:
        # Create keyboard with copy and delete buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Copy", 
                    copy_text=CopyTextButton(text=str(result))
                ),
                InlineKeyboardButton(
                    text="❌ Delete", 
                    callback_data="delete"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await msg.reply_text(display_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error sending message: {e}")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    result, display_text = await handle_calculation(query)
    
    results = []
    if result is not None:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"Result: {format_number(result)}",
                input_message_content=InputTextMessageContent(
                    display_text, parse_mode='HTML'
                ),
                description=f"{query} = {format_number(result)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="Copy", copy_text=CopyTextButton(text=str(result)))]
                ])
            )
        )
    
    await update.inline_query.answer(results, cache_time=0)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "delete":
        try:
            await query.message.delete()
        except Exception as e:
            logging.error(f"Error deleting message: {e}")

# Flask for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    
    # Handle regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handle Business messages
    application.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE & filters.TEXT, handle_message))
    
    # Handle Inline queries
    application.add_handler(InlineQueryHandler(inline_query))
    
    # Handle button callbacks
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot is starting with Inline and Business Mode support...")
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        # Keep the bot running
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
