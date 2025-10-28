import os, re, httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# تحميل التوكن من ملف .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

URL_RX = re.compile(r"(https?://[^\s]+)")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أرسل أي رابط من مواقع التواصل وسأعطيك خيارات التحميل.")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    m = URL_RX.search(text)
    if not m:
        await update.message.reply_text("❌ أرسل رابطًا صحيحًا.")
        return
    url = m.group(1)
    context.user_data["url"] = url

    buttons = [
        [InlineKeyboardButton("🎥 تحميل فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت من الفيديو", callback_data="audio")],
        [InlineKeyboardButton("🔊 ملف صوتي", callback_data="file")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("اختر نوع التحميل:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    url = context.user_data.get("url")

    await query.edit_message_text(f"جاري التحميل ({choice}) من الرابط:\n{url}\n⏳")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get("https://api.snapsave.io/", params={"url": url})
            data = r.json()

        if "medias" not in data or not data["medias"]:
            await query.message.reply_text("⚠️ لم أستطع جلب المحتوى.")
            return

        media_url = data["medias"][0]["url"]

        if choice == "video":
            await query.message.reply_video(video=media_url, caption="✅ تم تحميل الفيديو.")
        elif choice == "audio":
            await query.message.reply_audio(audio=media_url, caption="✅ تم تحميل الصوت.")
        else:
            await query.message.reply_document(document=media_url, caption="✅ تم تحميل الملف الصوتي.")

    except Exception as e:
        await query.message.reply_text(f"حدث خطأ أثناء التحميل: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
