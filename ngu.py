import requests
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio
import re

# ===== CONFIG =====
TOKEN = "6128053650:AAEBgN3wueM1A_T9lFKnM_VmSrEpTBz3uuc"
LOGIN_URL = "https://courses.ut.edu.vn/login/index.php"
CALENDAR_URL = "https://courses.ut.edu.vn/calendar/view.php"

user_state = {}
user_data = {}

# ================= START =================
async def start(update, context):
    await update.message.reply_text("✅ Bot OK\nGõ /login để nhập tài khoản")

# ================= LOGIN =================
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

        # ✅ lấy text sạch
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        title = lines[0] if len(lines) > 0 else "Không rõ"

        # ✅ lấy thời gian
        import re
        match = re.search(r'(\d{1,2} .*?, \d{1,2}:\d{2})', text)
        time_str = match.group(1) if match else "Không rõ"

        # ✅ lấy LINK + MÔN
        subject = "Không rõ"
        link = "Không có link"

        a_tag = e.find("a")

# ✅ lấy LINK + MÔN đúng
        a_tags = e.find_all("a")

        subject = "Không rõ"
        link = "Không có link"

        for a in a_tags:
            text_a = a.get_text(strip=True)

            if "[" in text_a and "]" in text_a:
                subject = text_a
                link = a.get("href")
                break

        subject = subject.split("]")[-1].strip()

        # ✅ output
        result += f"📌 {count}. {title}\n"
        result += f"⏰ Hạn: {time_str}\n"
        result += f"📚 Môn: {subject}\n"
        result += f"🔗 Link: {link}\n\n"

        count += 1

    result += "━━━━━━━━━━━━━━━━━━"

    return result
# ================= LOGIN + GET DATA =================
def get_calendar(username, password):
    try:
        session = requests.Session()

        # ✅ lấy token
        r = session.get(LOGIN_URL)
        soup = BeautifulSoup(r.text, "html.parser")

        token_input = soup.find("input", {"name": "logintoken"})
        if not token_input:
            return "❌ Không lấy được token"

        logintoken = token_input["value"]

        # ✅ login
        payload = {
            "username": username,
            "password": password,
            "logintoken": logintoken
        }

        r = session.post(LOGIN_URL, data=payload)

        if "loginerrors" in r.text.lower():
            return "❌ Sai tài khoản hoặc mật khẩu"

        # ✅ lấy calendar
        r = session.get(CALENDAR_URL)
        soup = BeautifulSoup(r.text, "html.parser")

        events = soup.find_all("div", class_="event")

        if not events:
            return breakpoint("❌ Không lấy được dữ liệu")
        return format_events(events)

    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input))

    print("✅ Bot đang chạy...")

    app.run_polling()

if __name__ == "__main__":
    main()