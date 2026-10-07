import os
import glob
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

# ================= تنظیمات اصلی =================
BOT_TOKEN = "8812916816:AAFpXmZeswyVSYml1LN58AqG2Calbz-3TYQ"
BOT_USERNAME = "downloadyoutube20bot"
CHANNEL_USERNAME = "@zhuug"
CHANNEL_LINK = "https://t.me/zhuug"
GAME_BOT_LINK = "https://t.me/PassorBazBot"
# ===============================================

def is_youtube_url(url: str) -> bool:
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    return any(domain in url.lower() for domain in youtube_domains)

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except TelegramError as e:
        print(f"خطا در بررسی عضویت: {e}")
        return False

def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم (بررسی مجدد)", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_reply_keyboard():
    """کیبورد پایین صفحه همراه با دکمه شروع مجدد"""
    keyboard = [
        [KeyboardButton("🔄 شروع مجدد")],
        [KeyboardButton("🎮 ورود به ربات بازی‌ها"), KeyboardButton("📢 کانال اصلی")],
        [KeyboardButton("ℹ️ راهنمای دانلود"), KeyboardButton("👥 ارسال به دوستان")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_video_inline_keyboard():
    share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=بهترین%20ربات%20دانلود%20رایگان%20از%20یوتیوب%20🎬"
    keyboard = [
        [InlineKeyboardButton("🎮 بازی شطرنج، مار و دوز (رایگان)", url=GAME_BOT_LINK)],
        [
            InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK),
            InlineKeyboardButton("🔄 ارسال به دوستان", url=share_url)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    is_member = await is_user_member(user_id, context)
    if not is_member:
        msg_text = (
            "سلام! خوش آمدید 🌸\n\n"
            "⚠️ برای استفاده رایگان از ربات، لطفاً ابتدا عضو کانال زیر شوید، "
            "سپس دکمه «عضو شدم» را بزنید:"
        )
        await update.message.reply_text(msg_text, reply_markup=get_join_keyboard())
        return

    welcome_text = (
        "سلام! به ربات دانلود از یوتیوب خوش آمدید 🎬\n\n"
        "🔗 کافیست لینک ویدیو یا Shorts یوتیوب را بفرستید تا سریع برایتان دانلود شود."
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_reply_keyboard())

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    is_member = await is_user_member(user_id, context)
    if is_member:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ عضویت شما تایید شد!\n\nحالا لینک ویدیوی یوتیوب را بفرستید 👇",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await query.answer("❌ هنوز عضو کانال نشده‌اید! ابتدا عضو شوید و سپس دکمه را بزنید.", show_alert=True)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # ۱. بررسی عضویت در کانال
    async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except TelegramError as e:
        print(f"❌ خطای بررسی عضویت: {e}")
        print("👉 اگر نوشته 'not enough rights' یعنی ربات ادمین کانال نشده.")
        print("👉 اگر نوشته 'chat not found' یعنی CHANNEL_USERNAME اشتباه است.")
        return False

    # ۲. دکمه شروع مجدد
    if text in ["🔄 شروع مجدد", "/start", "start", "شروع"]:
        await start_command(update, context)
        return

    elif text == "🎮 ورود به ربات بازی‌ها":
        await update.message.reply_text(f"🎲 برای بازی شطرنج، مار، دوز و... وارد ربات زیر شوید:\n\n👉 {GAME_BOT_LINK}")
        return

    elif text == "📢 کانال اصلی":
        await update.message.reply_text(f"📢 کانال رسمی ما:\n👉 {CHANNEL_LINK}")
        return

    elif text == "ℹ️ راهنمای دانلود":
        guide_text = (
            "📖 راهنما:\n\n"
            "۱. در یوتیوب گزینه Share (اشتراک‌گذاری) را بزنید و Copy link را انتخاب کنید.\n"
            "۲. لینک را داخل این ربات بفرستید تا ویدیو بلافاصله ارسال شود."
        )
        await update.message.reply_text(guide_text)
        return

    elif text == "👥 ارسال به دوستان":
        share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=دانلود%20رایگان%20و%20سریع%20فیلم%20از%20یوتیوب%20🎬"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 اشتراک‌گذاری با دوستان", url=share_url)]])
        await update.message.reply_text("برای معرفی ربات به دوستان روی دکمه زیر بزنید:", reply_markup=kb)
        return

    # ۳. دانلود یوتیوب
    if not is_youtube_url(text):
        await update.message.reply_text("❌ لطفاً یک لینک معتبر از یوتیوب بفرستید یا از دکمه‌های زیر استفاده کنید.")
        return

    status_msg = await update.message.reply_text("⏳ در حال دریافت و آماده‌سازی ویدیو از یوتیوب...")

    output_template = f"video_{user_id}_%(id)s.%(ext)s"
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
        'outtmpl': output_template,
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            title = info.get('title', 'ویدیوی یوتیوب')
            video_file = ydl.prepare_filename(info)

            caption = (
                f"🎬 {title}\n\n"
                f"⚡ دانلود رایگان: @{BOT_USERNAME}\n"
                f"♟ ربات بازی شطرنج و مار: @PassorBazBot\n"
                f"📢 کانال اصلی: {CHANNEL_USERNAME}"
            )

            await status_msg.edit_text("📤 در حال ارسال ویدیو...")
            with open(video_file, 'rb') as vf:
                await update.message.reply_video(
                    video=vf,
                    caption=caption,
                    reply_markup=get_video_inline_keyboard()
                )
            await status_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ خطا در دریافت ویدیو! لطفاً دوباره امتحان کنید.")

    finally:
        for f in glob.glob(f"video_{user_id}_*"):
            try:
                os.remove(f)
            except:
                pass

def main():
    print("ربات روشن شد...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    app.run_polling()

if __name__ == '__main__':
    main()
