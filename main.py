import asyncio
import logging
import os
import re
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==================================================
# تنظیمات عمومی
# ==================================================

BOT_TOKEN = os.environ.get("8812916816:AAFpXmZeswyVSYml1LN58AqG2Calbz-3TYQ")
BOT_USERNAME = "downloadyoutube20bot"

CHANNEL_USERNAME = "@zhuug"
CHANNEL_LINK = "https://t.me/zhuug"

GAME_BOT_LINK = "https://t.me/PassorBazBot"
IMDB_BOT_LINK = "https://t.me/mafia12robot"

MAX_FILE_SIZE = 48 * 1024 * 1024

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==================================================
# وب‌سرور سلامت Render
# ==================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
        self.end_headers()
        self.wfile.write(b"OK - SoundCloud bot is live")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(
        ("0.0.0.0", port),
        HealthCheckHandler,
    )

    logger.info("Health server started on port %s", port)
    server.serve_forever()


# ==================================================
# تشخیص و استخراج لینک
# ==================================================

def extract_url(text: str):
    """
    از متن Share ساندکلاد فقط لینک را جدا می‌کند.

    مثال:
    Listen to Track by Artist on #SoundCloud
    https://on.soundcloud.com/example
    """

    match = re.search(
        r"https?://[^\s<>\"']+",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    url = match.group(0).strip()
    url = url.rstrip(".,!?)]}>،؛")

    return url


def is_soundcloud_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False

    return (
        host == "soundcloud.com"
        or host.endswith(".soundcloud.com")
    )


# ==================================================
# عضویت اجباری
# ==================================================

async def is_user_member(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )

        return member.status in [
            "creator",
            "administrator",
            "member",
        ]

    except TelegramError as error:
        logger.error("Membership check error: %s", error)
        return False


def get_join_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "عضویت در کانال",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "عضو شدم؛ بررسی مجدد",
                    callback_data="check_join",
                )
            ],
        ]
    )


# ==================================================
# کیبوردهای ربات
# ==================================================

def get_main_reply_keyboard():
    keyboard = [
        [
            KeyboardButton("شروع مجدد"),
        ],
        [
            KeyboardButton("ربات فیلم و سریال IMDb"),
            KeyboardButton("ربات بازی‌ها"),
        ],
        [
            KeyboardButton("کانال اصلی"),
            KeyboardButton("ارسال به دوستان"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )


def get_audio_inline_keyboard():
    share_url = (
        "https://t.me/share/url"
        f"?url=https://t.me/{BOT_USERNAME}"
        "&text=دانلود رایگان آهنگ از ساندکلاد"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "معرفی فیلم و نمره IMDb",
                url=IMDB_BOT_LINK,
            )
        ],
        [
            InlineKeyboardButton(
                "بازی‌های تلگرامی",
                url=GAME_BOT_LINK,
            )
        ],
        [
            InlineKeyboardButton(
                "عضویت در کانال",
                url=CHANNEL_LINK,
            ),
            InlineKeyboardButton(
                "اشتراک‌گذاری",
                url=share_url,
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# دانلود SoundCloud
# ==================================================

def download_audio_task(
    url: str,
    workdir: str,
):
    output_template = os.path.join(
        workdir,
        "%(id)s.%(ext)s",
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "continuedl": True,
        "overwrites": True,
        "max_filesize": MAX_FILE_SIZE,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            url,
            download=True,
        )

        title = info.get(
            "title",
            "آهنگ ساندکلاد",
        )

        uploader = (
            info.get("artist")
            or info.get("uploader")
            or "SoundCloud"
        )

        file_path = None

        # پیدا کردن مسیر واقعی فایل دانلودشده
        requested_downloads = (
            info.get("requested_downloads")
            or []
        )

        for item in requested_downloads:
            possible_path = (
                item.get("filepath")
                or item.get("_filename")
            )

            if (
                possible_path
                and os.path.isfile(possible_path)
            ):
                file_path = possible_path
                break

        # روش دوم برای پیدا کردن فایل
        if not file_path:
            possible_path = ydl.prepare_filename(info)

            if os.path.isfile(possible_path):
                file_path = possible_path

        # روش سوم: جست‌وجوی فایل در پوشه
        if not file_path:
            downloaded_files = []

            for filename in os.listdir(workdir):
                full_path = os.path.join(
                    workdir,
                    filename,
                )

                if not os.path.isfile(full_path):
                    continue

                if filename.endswith(".part"):
                    continue

                downloaded_files.append(full_path)

            if downloaded_files:
                file_path = max(
                    downloaded_files,
                    key=os.path.getsize,
                )

        if not file_path:
            raise FileNotFoundError(
                "فایل دانلودشده پیدا نشد."
            )

        file_size = os.path.getsize(file_path)

        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                "حجم فایل بیشتر از محدودیت تلگرام است."
            )

        return {
            "title": title,
            "uploader": uploader,
            "file_path": file_path,
        }


# ==================================================
# دستورات
# ==================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if not await is_user_member(user_id, context):
        await update.message.reply_text(
            "سلام.\n\n"
            "برای استفاده از ربات ابتدا عضو کانال شوید "
            "و سپس دکمه «عضو شدم؛ بررسی مجدد» را بزنید.",
            reply_markup=get_join_keyboard(),
        )
        return

    await update.message.reply_text(
        "سلام.\n\n"
        "لینک آهنگ SoundCloud را بفرست.\n"
        "حتی اگر متن Share کامل ساندکلاد را بفرستی، "
        "ربات لینک را از داخل آن جدا می‌کند.",
        reply_markup=get_main_reply_keyboard(),
    )


async def check_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await is_user_member(user_id, context):
        try:
            await query.message.delete()
        except TelegramError:
            pass

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "عضویت تأیید شد.\n"
                "حالا لینک آهنگ SoundCloud را بفرست."
            ),
            reply_markup=get_main_reply_keyboard(),
        )
    else:
        await query.answer(
            "هنوز عضو کانال نشده‌اید.",
            show_alert=True,
        )


# ==================================================
# پردازش پیام‌ها
# ==================================================

async def handle_text_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not await is_user_member(user_id, context):
        await update.message.reply_text(
            "ابتدا باید عضو کانال باشید.",
            reply_markup=get_join_keyboard(),
        )
        return

    # دکمه‌های منو
    if text in [
        "شروع مجدد",
        "🔄 شروع مجدد",
        "start",
    ]:
        await start_command(update, context)
        return

    if text in [
        "ربات فیلم و سریال IMDb",
        "🎬 ربات فیلم و سریال (IMDb)",
    ]:
        await update.message.reply_text(
            "ربات جست‌وجوی مشخصات فیلم و سریال:\n"
            f"{IMDB_BOT_LINK}"
        )
        return

    if text in [
        "ربات بازی‌ها",
        "🎮 ربات بازی‌ها",
    ]:
        await update.message.reply_text(
            "ربات بازی‌های تلگرامی:\n"
            f"{GAME_BOT_LINK}"
        )
        return

    if text in [
        "کانال اصلی",
        "📢 کانال اصلی",
    ]:
        await update.message.reply_text(
            "کانال اصلی:\n"
            f"{CHANNEL_LINK}"
        )
        return

    if text in [
        "ارسال به دوستان",
        "👥 ارسال به دوستان",
    ]:
        share_url = (
            "https://t.me/share/url"
            f"?url=https://t.me/{BOT_USERNAME}"
            "&text=دانلود رایگان آهنگ از ساندکلاد"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "اشتراک‌گذاری ربات",
                        url=share_url,
                    )
                ]
            ]
        )

        await update.message.reply_text(
            "برای معرفی ربات به دوستان روی دکمه زیر بزنید:",
            reply_markup=keyboard,
        )
        return

    # استخراج فقط URL از متن
    url = extract_url(text)

    if not url:
        await update.message.reply_text(
            "لطفاً یک لینک SoundCloud ارسال کن."
        )
        return

    if not is_soundcloud_url(url):
        await update.message.reply_text(
            "این لینک مربوط به SoundCloud نیست."
        )
        return

    status_message = await update.message.reply_text(
        "در حال دانلود آهنگ از SoundCloud..."
    )

    workdir = tempfile.mkdtemp(
        prefix=f"soundcloud_{user_id}_"
    )

    try:
        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            None,
            download_audio_task,
            url,
            workdir,
        )

        title = result["title"]
        uploader = result["uploader"]
        file_path = result["file_path"]

        caption = (
            f"{title}\n"
            f"هنرمند: {uploader}\n\n"
            f"دانلودر: @{BOT_USERNAME}\n"
            f"ربات بازی‌ها: @PassorBazBot\n"
            f"کانال: {CHANNEL_USERNAME}"
        )

        await status_message.edit_text(
            "دانلود انجام شد؛ در حال ارسال فایل..."
        )

        # ارسال به‌صورت موزیک
        try:
            with open(file_path, "rb") as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title[:64],
                    performer=uploader[:64],
                    caption=caption[:1024],
                    reply_markup=get_audio_inline_keyboard(),
                )

        # اگر فرمت توسط Telegram به‌عنوان Audio پذیرفته نشد،
        # به‌صورت فایل معمولی ارسال می‌شود.
        except Exception as audio_error:
            logger.warning(
                "send_audio failed: %s",
                audio_error,
            )

            with open(file_path, "rb") as document_file:
                await update.message.reply_document(
                    document=document_file,
                    caption=caption[:1024],
                    reply_markup=get_audio_inline_keyboard(),
                )

        try:
            await status_message.delete()
        except TelegramError:
            pass

    except yt_dlp.utils.DownloadError as error:
        logger.error("yt-dlp error: %s", error)

        await status_message.edit_text(
            "دانلود انجام نشد.\n"
            "ممکن است آهنگ حذف شده، خصوصی یا محدود باشد."
        )

    except ValueError as error:
        logger.error("File size error: %s", error)

        await status_message.edit_text(
            str(error)
        )

    except Exception as error:
        logger.exception("Unexpected error: %s", error)

        error_text = str(error)

        await status_message.edit_text(
            "در پردازش آهنگ خطایی رخ داد:\n"
            f"{error_text[:300]}"
        )

    finally:
        shutil.rmtree(
            workdir,
            ignore_errors=True,
        )


# ==================================================
# اجرای ربات
# ==================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "متغیر BOT_TOKEN در Environment Render تنظیم نشده است."
        )

    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True,
    )
    health_thread.start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            check_join_callback,
            pattern="^check_join$",
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_messages,
        )
    )

    logger.info("SoundCloud bot is running...")
    application.run_polling(
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
