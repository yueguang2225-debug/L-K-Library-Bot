import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Logging ပြုလုပ်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# အချက်အလက်များ
TOKEN = "8782021971:AAFCVu4aUkJ-ZAI3wNY1e01iXlOm2cWFteA"
ADMIN_ID = 8012437507
MUST_JOIN_CHANNEL = "@collectionroom305"

# Flask Web Server
app = Flask(__name__)

@app.route('/')
def home():
    return "PDF Bot is running and alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Memory ထဲတွင် PDF ဖိုင်များ သိမ်းဆည်းရန် Data Structure
pdf_database = {}

# Channel Join ထားခြင်း ရှိ/မရှိ စစ်ဆေးသည့် Function
async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=MUST_JOIN_CHANNEL, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        return True

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    joined = await is_user_joined(context, user_id)
    if not joined:
        channel_link = MUST_JOIN_CHANNEL.replace('@', '')
        keyboard = [
            [InlineKeyboardButton("📢 Channel သို့ ဝင်ရန်", url=f"https://t.me/{channel_link}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ **သတိပေးချက်!**\n\nBot ကို အသုံးပြုနိုင်ရန်အတွက် ကျေးဇူးပြု၍ ကျွန်ုပ်တို့၏ Channel {MUST_JOIN_CHANNEL} ကို မဖြစ်မနေ Join ပေးပါရန်။",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ! PDF ရှာဖွေရေး Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သင်ရှာဖွေလိုသော PDF ဖိုင်အမည်ကို ရိုက်ပို့ပေးပါ။"
    )

# PDF ဖိုင် ထည့်သွင်းခြင်း (Admin သာလျှင်)
async def add_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ သင်သည် Admin မဟုတ်ပါသဖြင့် ဤ Command ကို သုံးပိုင်ခွင့်မရှိပါ။")
        return

    if not update.message.document or update.message.document.mime_type != 'application/pdf':
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ PDF ဖိုင်တစ်ခုကို ပေးပို့ပြီး Caption တွင် `/addpdf <ဖိုင်အမည်>` ဟု ရေးပေးပါ။")
        return

    file_name = " ".join(context.args).strip().lower()
    if not file_name:
        file_name = update.message.document.file_name.replace(".pdf", "").strip().lower()

    file_id = update.message.document.file_id
    pdf_database[file_name] = file_id
    
    await update.message.reply_text(f"✅ PDF ဖိုင်ကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!\n\n📄 **ဖိုင်အမည်:** `{file_name}`", parse_mode="Markdown")

# စာသားဖြင့် PDF ရှာဖွေခြင်း သို့မဟုတ် Admin မှ PDF လက်ခံခြင်း
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Channel Check
    joined = await is_user_joined(context, user_id)
    if not joined:
        channel_link = MUST_JOIN_CHANNEL.replace('@', '')
        keyboard = [
            [InlineKeyboardButton("📢 Channel သို့ ဝင်ရန်", url=f"https://t.me/{channel_link}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ Bot ကို အသုံးပြုရန် Channel {MUST_JOIN_CHANNEL} ကို Join ပေးပါရန်။",
            reply_markup=reply_markup
        )
        return

    # Admin မှ PDF တိုက်ရိုက် ပို့လာပါက
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        if user_id == ADMIN_ID:
            caption = update.message.caption or ""
            if caption.startswith("/addpdf"):
                file_name = caption.replace("/addpdf", "").strip().lower()
            else:
                file_name = update.message.document.file_name.replace(".pdf", "").strip().lower()
            
            file_id = update.message.document.file_id
            pdf_database[file_name] = file_id
            await update.message.reply_text(f"✅ PDF မှတ်တမ်းတင်ပြီးပါပြီ - `{file_name}`", parse_mode="Markdown")
            return

    # စာသားဖြင့် ရှာဖွေခြင်း
    if update.message.text:
        query = update.message.text.strip().lower()
        if query in pdf_database:
            file_id = pdf_database[query]
            await update.message.reply_document(document=file_id, caption=f"📄 {query}.pdf")
        else:
            matches = [k for k in pdf_database.keys() if query in k]
            if matches:
                text = "🔎 သင်ရှာဖွေသော အမည်နှင့် ဆင်တူသည့် ဖိုင်များ:\n\n"
                for m in matches:
                    text += f"• `{m}`\n"
                text += "\nအတိအကျ ပြန်လည် ရိုက်ပို့ပေးပါရန်။"
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ ရှာဖွေနေသော PDF ဖိုင်ကို မတွေ့ရှိပါ။ ဖိုင်အမည် အမှန်ကို ပြန်လည် စစ်ဆေးပေးပါရန်။")

# PDF ဖိုင်များစာရင်း ကြည့်ခြင်း (Admin သာ)
async def list_pdfs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not pdf_database:
        await update.message.reply_text("📂 လက်ရှိ သိမ်းဆည်းထားသော PDF ဖိုင် မရှိသေးပါ။")
        return
    
    text = "📚 **သိမ်းဆည်းထားသော PDF ဖိုင်များ စာရင်း:**\n\n"
    for i, name in enumerate(pdf_database.keys(), 1):
        text += f"{i}. `{name}`\n"
        
    await update.message.reply_text(text, parse_mode="Markdown")

# PDF ဖိုင် ဖျက်ခြင်း (Admin သာ)
async def del_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    file_name = " ".join(context.args).strip().lower()
    if file_name in pdf_database:
        del pdf_database[file_name]
        await update.message.reply_text(f"🗑️ `{file_name}` ကို အောင်မြင်စွာ ဖျက်ပြီးပါပြီ။", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ အဆိုပါ ဖိုင်အမည်ကို မတွေ့ရှိပါ။")

def main():
    # Flask ဆာဗာကို Thread ဖြင့် စတင်ခြင်း
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram Bot App
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("addpdf", add_pdf_command))
    app_bot.add_handler(CommandHandler("pdflist", list_pdfs))
    app_bot.add_handler(CommandHandler("delpdf", del_pdf))
    app_bot.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    logging.info("Bot is polling...")
    app_bot.run_polling()

if __name__ == '__main__':
    main()
