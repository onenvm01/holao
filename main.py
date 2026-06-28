import requests
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler
import os

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")

CALENDAR_URL = "https://courses.ut.edu.vn/calendar/view.php"

COOKIE = {
    "MoodleSession": "DAN_COOKIE_CUA_BAN"
}

# ================= CHECK STATUS =================
def check_status():
    try:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        session.cookies.update(COOKIE)

        r = session.get(CALENDAR_URL, headers=headers, timeout=10)

        if r.status_code != 200:
            return f"❌ Web lỗi: {r.status_code}"

        if "login" in r.url.lower():
            return "❌ Cookie hết hạn"

        return "✅ Web OK (cookie hoạt động)"

    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# ================= GET CALENDAR =================
def get_calendar():
    try:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        session.cookies.update(COOKIE)

        r = session.get(CALENDAR_URL, headers=headers)

        if "login" in r.url.lower():
            return "❌ Cookie hết hạn"

        soup = BeautifulSoup(r.text, "html.parser")
        events = soup.find_all("div", class_="event")

        if not events:
            return "❌ Không lấy được dữ liệu"

        result = "📅 DEADLINE:\n\n"

        for e in events[:5]:  # ✅ lấy 5 cái cho gọn test
            text = e.get_text(strip=True)
            result += f"• {text}\n\n"

        return result

    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# ================= COMMAND =================
async def start(update, context):
    status = check_status()

    await update.message.reply_text(f"✅ Bot chạy\n\n{status}")

async def test(update, context):
    await update.message.reply_text("⏳ Đang test...")

    data = get_calendar()

    await update.message.reply_text(data[:4000])

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    print("✅ BOT TEST RUNNING")

    app.run_polling()

if __name__ == "__main__":
    main()
