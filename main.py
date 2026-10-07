import os
import glob
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters, 
    ContextTypes
)
from telegram.error import TelegramError
import yt_dlp

# ================= تنظیمات وب‌سرور برای پاس کردن پورت رندر =================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"OK - Bot is Live 24/7")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # جلوگیری از شلوغ شدن لاگ رندر

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()
# =========================================================================

# ================= تنظیمات ربات =================
BOT_TOKEN = "8812916816:AAFpXmZeswyVSYml1LN58AqG2Calbz-3TYQ"
BOT_USERNAME = "downloadyoutube20bot"

# کانال عضویت اجباری
CHANNEL_USERNAME = "@zhuug"
CHANNEL_LINK = "https://t.me/zhuug"

# ربات‌های تبلیغاتی
GAME_BOT_LINK = "https://t.me/PassorBazBot"
IMDB_BOT_LINK = "https://t.me/mafia12robot"
# ===============================================

def is_soundcloud_url(url: str) -> bool:
    return any(d in url.lower() for d in ['soundcloud.com', 'on.soundcloud.com'])

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except TelegramError as e:
        print(f"Error checking member: {e}")
        return False

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم (بررسی مجدد)", callback_data="check_join")]
    ])

def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("🔄 شروع مجدد")],
        [KeyboardButton("🎬 ربات فیلم و سریال (IMDb)"), KeyboardButton("🎮 ربات بازی‌ها")],
        [KeyboardButton("📢 کانال اصلی"), KeyboardButton("👥 ارسال به دوستان")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_audio_inline_keyboard():
    share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=دانلود%20رایگان%20آهنگ%20از%20ساندکلاد%20🎧"
    keyboard = [
        [InlineKeyboardButton("🎬 معرفی فیلم و نمره IMDb", url=IMDB_BOT_LINK)],
        [InlineKeyboardButton("🎮 بازی شطرنج، مار و دوز", url=GAME_BOT_LINK)],
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK), InlineKeyboardButton("🔄 اشتراک‌گذاری", url=share_url)]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(user_id, context):
        await update.message.reply_text(
            "سلام! برای استفاده رایگان لطفاً ابتدا عضو کانال ما شوید و سپس «عضو شدم» را بزنید:",
            reply_markup=get_join_keyboard()
        )
        return

    await update.message.reply_text(
        "🎧 سلام! لینک آهنگ ساندکلاد (SoundCloud) را بفرست تا با بالاترین کیفیت دانلود کنم.",
        reply_markup=get_main_reply_keyboard()
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_member(user_id, context):
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ عضویت تایید شد! حالا لینک آهنگ ساندکلاد را بفرستید 👇",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await query.answer("❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

def download_audio_task(url: str, output_template: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'آهنگ ساندکلاد')
        uploader = info.get('uploader', 'SoundCloud')
        filename = ydl.prepare_filename(info)
        return title, uploader, filename

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not await is_user_member(user_id, context):
        await update.message.reply_text("⚠️ اول باید عضو کانال باشید:", reply_markup=get_join_keyboard())
        return

    if text in ["🔄 شروع مجدد", "/start", "start"]:
        await start_command(update, context)
        return
    elif text == "🎬 ربات فیلم و سریال (IMDb)":
        await update.message.reply_text(f"🍿 ربات جستجوی مشخصات فیلم و سریال:\n👉 {IMDB_BOT_LINK}")
        return
    elif text == "🎮 ربات بازی‌ها":
        await update.message.reply_text(f"🎲 ربات بازی‌های تلگرامی ما:\n👉 {GAME_BOT_LINK}")
        return
    elif text == "📢 کانال اصلی":
        await update.message.reply_text(f"📢 کانال ما:\n👉 {CHANNEL_LINK}")
        return
    elif text == "👥 ارسال به دوستان":
        share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=دانلود%20رایگان%20آهنگ%20از%20ساندکلاد%20🎧"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 اشتراک‌گذاری ربات", url=share_url)]])
        await update.message.reply_text("برای معرفی ربات به دوستان کلیک کنید:", reply_markup=kb)
        return

    if not is_soundcloud_url(text):
        await update.message.reply_text("❌ لطفاً فقط لینک معتبر از ساندکلاد (SoundCloud) ارسال کنید.")
        return

    status_msg = await update.message.reply_text("⏳ در حال دریافت آهنگ از ساندکلاد...")
    output_template = f"audio_{user_id}_%(id)s.%(ext)s"

    try:
        loop = asyncio.get_running_loop()
        title, uploader, audio_file = await loop.run_in_executor(None, download_audio_task, text, output_template)

        caption = (
            f"🎧 {title}\n"
            f"👤 خواننده/سازنده: {uploader}\n\n"
            f"⚡ دانلودر: @{BOT_USERNAME}\n"
            f"♟ بازی‌ها: @PassorBazBot\n"
            f"📢 کانال ما: {CHANNEL_USERNAME}"
        )

        await status_msg.edit_text("📤 در حال ارسال موزیک به تلگرام...")
        with open(audio_file, 'rb') as af:
            await update.message.reply_audio(
                audio=af,
                title=title[:60],
                performer=uploader[:60],
                caption=caption,
                reply_markup=get_audio_inline_keyboard()
            )
        await status_msg.delete()

    except Exception as e:
        err = str(e)
        print(f"Error: {err}")
        if "max_filesize" in err.lower() or "too large" in err.lower():
            await status_msg.edit_text("❌ حجم فایل بالای ۴۸ مگابایت است.")
        else:
            await status_msg.edit_text(f"❌ خطا در دانلود موزیک:\n{err[:250]}")
    finally:
        for f in glob.glob(f"audio_{user_id}_*"):
            try:
                os.remove(f)
            except:
                pass

def main():
    # ۱. اجرای وب‌سرور برای زنده نگه داشتن رندر
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    print("ربات آنلاین شد...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.run_polling()

if __name__ == '__main__':
    main()
