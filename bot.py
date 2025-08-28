# bot.py — SmartFaith MVP Bot (safe version)
import os, sys, random, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    print("⚠️  Env TELEGRAM_TOKEN belum di-set. Set dulu via $env:TELEGRAM_TOKEN atau setx.")
    sys.exit(1)
DEFAULT_CITY = "Palembang"
APP_URL = "https://smartfaith.streamlit.app"

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"[START] {user.username} ({user.id})")
    await update.message.reply_text(
        "Assalamu’alaikum 👋\n"
        "Selamat datang di SmartFaith Bot ✨\n\n"
        "Asisten Islami digital:\n"
        "• Jadwal Shalat\n"
        "• Hitung Zakat\n"
        "• Doa Harian\n"
        "• Murottal\n"
        "• Setor Hafalan\n"
        "• Buka sebagai Mini App (in-Telegram WebView)\n\n"
        "Versi lengkap (web): https://smartfaith.streamlit.app\n"
        "Ketik /help untuk daftar perintah."
    )

async def help_cmd(update, context):
    text = (
        "📖 Daftar Perintah:\n"
        "/salat [kota] — Jadwal shalat (default Palembang)\n"
        "/zakat <nominal> — Hitung zakat 2.5%\n"
        "/doa — Doa harian acak\n"
        "/murottal — Link murottal random\n"
        "/hafalan <label> | <teks> — Simpan setoran hafalan\n"
        "/hafalan_progress — Lihat riwayat setoran\n"
        "/app — Buka SmartFaith sebagai Mini App\n"
    )
    await update.message.reply_text(text)

async def salat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) or DEFAULT_CITY
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Indonesia&method=2"
        r = requests.get(url, timeout=10).json()
        data = r["data"]["timings"]
        lines = [f"{k}: {data[k]}" for k in ["Fajr","Dhuhr","Asr","Maghrib","Isha"]]
        await update.message.reply_text(f"🕌 Jadwal Shalat {city.title()}\n" + "\n".join(lines))
    except Exception:
        await update.message.reply_text(f"⚠️ Gagal ambil jadwal untuk {city}. Coba lagi nanti ya.")

async def zakat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Format: /zakat 1000000")
    try:
        nominal = int(context.args[0].replace(".","").replace(",",""))
        zakatnya = int(nominal * 2.5 / 100)
        await update.message.reply_text(f"💰 Zakat dari Rp {nominal:,} = Rp {zakatnya:,}".replace(",", "."))
    except:
        await update.message.reply_text("⚠️ Nominal harus berupa angka.")

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
    text = update.message.text
    if "|" not in text:
        return await update.message.reply_text("Format: /hafalan <label> | <teks>")
    _, payload = text.split(" ", 1)
    label, isi = [p.strip() for p in payload.split("|", 1)]
    uid = update.effective_user.id
    HAFALAN.setdefault(uid, []).append((label, isi))
    await update.message.reply_text("✅ Hafalan tersimpan.")

async def hafalan_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    history = HAFALAN.get(uid, [])
    if not history:
        return await update.message.reply_text("Belum ada setoran hafalan.")
    lines = [f"• {l} — {len(t)} huruf" for l,t in history[-5:]]
    await update.message.reply_text("📒 Riwayat Hafalan:\n" + "\n".join(lines))

async def open_app(update, context):
    kb = [
        [InlineKeyboardButton(text="🔷 Buka SmartFaith (Mini App)", web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton(text="🌐 Buka di Browser", url=APP_URL)],
    ]
    await update.message.reply_text("Pilih cara membuka SmartFaith:", reply_markup=InlineKeyboardMarkup(kb))

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Tidak dikenali. Ketik /help untuk daftar perintah.")

def main():
    app = Application.builder().token(TOKEN).build()
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
    print("✅ SmartFaith Bot jalan (MVP)...")
    app.run_polling()

if __name__ == "__main__":
    main()