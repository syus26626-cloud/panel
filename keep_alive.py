from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Renderが割り当てるポート（デフォルトは3000）で起動
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Botのメイン処理を邪魔しないように、別スレッドでFlaskをバックグラウンド実行
    t = Thread(target=run, daemon=True)
    t.start()
