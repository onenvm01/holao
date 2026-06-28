import requests
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio
import re
import os
import sys

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")  # ✅ dùng env (Railway)

if not TOKEN:
    raise ValueError("❌ TOKEN chưa được set")

LOGIN_URL = "https://courses.ut.edu.vn/login/index.php"
CALENDAR_URL = "https://courses.ut.edu.vn/calendar/view.php"

user_state = {}
user_data = {}

# ================= START =================
async def start(update, context):
    await update.message.reply_text("✅ Bot OK\nGõ /login để nhập tài khoản")

# ================= LOGIN COMMAND =================
async def login_command(update, context):
    user_id = update.effective_user.id
    user_state[user_id] = "WAIT_USERNAME"
    await update.message.reply_text("👉 Nhập username:")

# ================= HANDLE INPUT =================
async def handle_input(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    if user_state[user_id] == "WAIT_USERNAME":
        user_data[user_id] = {"username": text}
        user_state[user_id] = "WAIT_PASSWORD"
        await update.message.reply_text("👉 Nhập password:")

    elif user_state[user_id] == "WAIT_PASSWORD":
        user_data[user_id]["password"] = text
        user_state.pop(user_id)

        await update.message.reply_text("⏳ Đang login và lấy lịch...")

        result = get_calendar(
            user_data[user_id]["username"],
            user_data[user_id]["password"]
        )

        await update.message.reply_text(result[:4000])

# ================= FORMAT =================
def format_events(events):
    result = "📅 DANH SÁCH DEADLINE\n\n━━━━━━━━━━━━━━━━━━\n\n"

    count = 1

    for e in events:
        text = e.get_text()

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # ✅ tìm title
        title = "Không rõ"
        for line in lines:
            if "tới hạn" in line or "due" in line:
                title = line
                break
        if title == "Không rõ" and lines:
            title = lines[0]

        # ✅ time
        match = re.search(r'(\d{1,2} .*?, \d{1,2}:\d{2})', text)
        time_str = match.group(1) if match else "Không rõ"

        # ✅ subject + link đúng
        subject = "Không rõ"
        link = "Không có link"

        a_tags = e.find_all("a")

        for a in a_tags:
            text_a = a.get_text(strip=True)
            if "[" in text_a and "]" in text_a:
                subject = text_a.split("]")[-1].strip()
                link = a.get("href")
                break

        result += f"📌 {count}. {title}\n"
        result += f"⏰ Hạn: {time_str}\n"
        result += f"📚 Môn: {subject}\n"
        result += f"🔗 {link}\n\n"

        count += 1

    result += "━━━━━━━━━━━━━━━━━━"

    return result

# ================= LOGIN + GET CALENDAR =================
def get_calendar(username, password):
    try:
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # ✅ lấy token
        r = session.get(LOGIN_URL, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        token_input = soup.find("input", {"name": "logintoken"})
        if not token_input:
            return "❌ Không lấy được logintoken (bị chặn hoặc web đổi)"

        logintoken = token_input["value"]

        # ✅ login
        payload = {
            "username": username,
            "password": password,
            "logintoken": logintoken
        }

        r = session.post(LOGIN_URL, data=payload, headers=headers)

        if "loginerrors" in r.text.lower():
            return "❌ Sai tài khoản hoặc mật khẩu"

        # ✅ calendar
        r = session.get(CALENDAR_URL, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        events = soup.find_all("div", class_="event")

        if not events:
            return "❌ Không lấy được deadline"

        return format_events(events)

    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# ================= MAIN =================
def main():

    # ✅ fix Windows (KHÔNG ảnh hưởng Railway)
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input))

    print("✅ Bot đang chạy...")

    app.run_polling()

if __name__ == "__main__":
    main()
