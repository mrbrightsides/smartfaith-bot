from flask import Flask
from threading import Thread
import os

def start():
    app = Flask(__name__)

    @app.get("/")
    def root():
        return "SmartFaith Bot up ✅"

    @app.get("/health")
    def health():
        return "ok", 200

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def run_in_thread():
    t = Thread(target=start, daemon=True)
    t.start()
