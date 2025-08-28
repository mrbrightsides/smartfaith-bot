import os, sys, random, logging, requests, signal, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from keep_alive import run_in_thread as keep_alive

# ---------- Config ----------
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("smartfaith")

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    print("⚠️  TELEGRAM_TOKEN belum di-set (Replit → Tools → Secrets).")
    sys.exit(1)

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Palembang")
APP_URL = os.getenv("APP_URL", "https://smartfaith.streamlit.app")
HTTP_TIMEOUT = 10

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    log.info("[START] %s (%s)", u.username, u.id)
    await update.message.reply_text(
        "Assalamu’alaikum 👋\n"
        "Selamat datang di SmartFaith Bot ✨\n\n"
        "• Jadwal Shalat • Zakat • Doa • Murottal • Hafalan • Mini App\n\n"
        f"Versi web: {APP_URL}\nKetik /help untuk daftar perintah."
    )

async def help_cmd(update, context):
    await update.message.reply_text(
        "📖 Perintah:\n"
        "/salat [kota]\n"
        "/zakat <nominal>\n"
        "/doa\n"
        "/murottal\n"
        "/hafalan <label> | <teks>\n"
        "/hafalan_progress\n"
        "/app"
    )

async def salat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args).strip() or DEFAULT_CITY
    try:
        url = ("https://api.aladhan.com/v1/timingsByCity"
               f"?city={city}&country=Indonesia&method=2")
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        data = r.json()["data"]["timings"]
        rows = [f"{k}: {data[k]}" for k in ["Fajr","Dhuhr","Asr","Maghrib","Isha"]]
        await update.message.reply_text(f"🕌 {city.title()}\n" + "\n".join(rows))
    except Exception as e:
        log.warning("jadwal %s gagal: %s", city, e)
        await update.message.reply_text(f"⚠️ Gagal ambil jadwal {city}. Coba lagi ya.")

async def zakat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Format: /zakat 1000000")
    try:
        nominal = int(context.args[0].replace(".","").replace(",",""))
        zakatnya = int(nominal * 2.5 / 100)
        await update.message.reply_text(
            f"💰 Zakat dari Rp {nominal:,} = Rp {zakatnya:,}".replace(",", "."))
    except:
        await update.message.reply_text("⚠️ Nominal harus angka.")

async def doa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doa_list = [
        "رَبِّ زِدْنِي عِلْمًا",
        "اللَّهُمَّ اغْفِرْ لِي وَلِوَالِدَيَّ وَارْحَمْهُمَا",
        "رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي",
    ]
    await update.message.reply_text("📿 Doa harian:\n\n" + random.choice(doa_list))

MUROTTAL = [
    ("Mishary Alafasy", "https://server8.mp3quran.net/afs/001.mp3"),
    ("Abdul Basit", "https://server6.mp3quran.net/basit/001.mp3"),
    ("Saad Al-Ghamdi", "https://server7.mp3quran.net/s_gmd/001.mp3"),
]
async def murottal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name, url = random.choice(MUROTTAL)
    await update.message.reply_text(f"🎧 Murottal {name}\n{url}")

HAFALAN = {}
async def hafalan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if "|" not in text:
        return await update.message.reply_text("Format: /hafalan <label> | <teks>")
    try:
        _, payload = text.split(" ", 1)
        label, isi = [p.strip() for p in payload.split("|", 1)]
    except ValueError:
        return await update.message.reply_text("Format: /hafalan <label> | <teks>")
    uid = update.effective_user.id
    HAFALAN.setdefault(uid, []).append((label, isi))
    await update.message.reply_text("✅ Hafalan tersimpan.")

async def hafalan_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    hist = HAFALAN.get(uid, [])
    if not hist:
        return await update.message.reply_text("Belum ada setoran hafalan.")
    lines = [f"• {l} — {len(t)} huruf" for l, t in hist[-5:]]
    await update.message.reply_text("📒 Riwayat Hafalan:\n" + "\n".join(lines))

async def open_app(update, context):
    kb = [
        [InlineKeyboardButton("🔷 Buka SmartFaith (Mini App)", web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton("🌐 Buka di Browser", url=APP_URL)],
    ]
    await update.message.reply_text("Pilih cara membuka SmartFaith:", reply_markup=InlineKeyboardMarkup(kb))

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Tidak dikenali. Ketik /help untuk daftar perintah.")

def build_app():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler(["salat","shalat"], salat))
    app.add_handler(CommandHandler("zakat", zakat))
    app.add_handler(CommandHandler("doa", doa))
    app.add_handler(CommandHandler("murottal", murottal))
    app.add_handler(CommandHandler("hafalan", hafalan))
    app.add_handler(CommandHandler("hafalan_progress", hafalan_progress))
    app.add_handler(CommandHandler("app", open_app))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))
    return app

def main():
    # start tiny web server (for UptimeRobot ping)
    keep_alive()
    log.info("✅ SmartFaith Bot starting (Replit long-polling)…")
    app = build_app()
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        stop_signals=(signal.SIGINT, signal.SIGTERM, signal.SIGABRT),
    )

if __name__ == "__main__":
    main()
