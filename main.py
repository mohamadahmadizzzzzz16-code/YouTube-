import os
import glob
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

# ================= سرور کوچک برای رفع خطای پورت رندر =================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()
# ===================================================================

# ================= تنظیمات ربات =================
BOT_TOKEN = "8812916816:AAFpXmZeswyVSYml1LN58AqG2Calbz-3TYQ"
BOT_USERNAME = "downloadyoutube20bot"

CHANNEL_USERNAME = "@zhuug"
CHANNEL_LINK = "https://t.me/zhuug"

GAME_BOT_LINK = "https://t.me/PassorBazBot"
IMDB_BOT_LINK = "https://t.me/mafia12robot"
# ===============================================

def is_youtube_url(url: str) -> bool:
    return any(d in url.lower() for d in ['youtube.com', 'youtu.be', 'm.youtube.com'])

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

def get_video_inline_keyboard():
    share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=دانلود%20رایگان%20از%20یوتیوب%20🎬"
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
        "🎬 سلام! لینک ویدیوی یوتیوب یا Shorts را بفرست تا دانلود کنم.",
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
            text="✅ عضویت تایید شد! حالا لینک ویدیو را بفرستید 👇",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await query.answer("❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

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
        share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=دانلود%20رایگان%20از%20یوتیوب%20🎬"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 اشتراک‌گذاری ربات", url=share_url)]])
        await update.message.reply_text("برای معرفی ربات به دوستان کلیک کنید:", reply_markup=kb)
        return

    if not is_youtube_url(text):
        await update.message.reply_text("❌ لطفاً فقط لینک یوتیوب ارسال کنید.")
        return

    status_msg = await update.message.reply_text("⏳ در حال دریافت ویدیو از یوتیوب...")
    output_template = f"video_{user_id}_%(id)s.%(ext)s"

    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
        'outtmpl': output_template,
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'web_embedded', 'ios'],
                'player_skip': ['webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV; Maple2012) AppleWebKit/534.7 (KHTML, like Gecko) SmartTV Safari/536.2'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            title = info.get('title', 'ویدیوی یوتیوب')
            video_file = ydl.prepare_filename(info)

            caption = (
                f"🎬 {title}\n\n"
                f"⚡ دانلودر: @{BOT_USERNAME}\n"
                f"♟ بازی‌ها: @PassorBazBot\n"
                f"📢 کانال ما: {CHANNEL_USERNAME}"
            )

            await status_msg.edit_text("📤 در حال ارسال به تلگرام...")
            with open(video_file, 'rb') as vf:
                await update.message.reply_video(
                    video=vf,
                    caption=caption,
                    reply_markup=get_video_inline_keyboard()
                )
            await status_msg.delete()
    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ حجم ویدیو بالای ۵۰ مگابایت است یا دریافت نشد.")
    finally:
        for f in glob.glob(f"video_{user_id}_*"):
            try:
                os.remove(f)
            except:
                pass

def main():
    # روشن کردن سرور وب در پس‌زمینه برای راضی کردن رندر
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    print("ربات آنلاین شد...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.run_polling()

if __name__ == '__main__':
    main()
