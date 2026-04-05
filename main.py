import os
import sqlite3
import subprocess
import asyncio
from flask import Flask, render_template, request, jsonify
from telethon import TelegramClient, events

# --- НАСТРОЙКИ ---
API_ID = 30871632
API_HASH = '346a8b2392f05c8fed89072970faf3e1'
DB_PATH = 'database.db'
SESSION_PATH = 'bank_account' # Render подхватит твой файл .session

app = Flask(__name__)
client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, status TEXT)')
    conn.commit()
    conn.close()

# Мониторинг подарков (работает в фоне)
@client.on(events.NewMessage)
async def handler(event):
    if event.gift:
        print(f"🎁 Получен подарок от {event.sender_id}")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO inventory (user_id, status) VALUES (?, ?)", (event.sender_id, 'available'))
        conn.commit()
        conn.close()

# --- СТРАНИЦЫ САЙТА ---

@app.route('/')
def index():
    # ТЕПЕРЬ ОН БУДЕТ ОТКРЫВАТЬ ТВОЙ index.html ИЗ ПАПКИ templates
    return render_template('index.html')

@app.route('/api/my_gifts')
def my_gifts():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify([])
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    gifts = conn.execute('SELECT * FROM inventory WHERE user_id = ? AND status = "available"', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(g) for g in gifts])

# Запуск клиента Telegram
async def run_bot():
    await client.start()
    print("🚀 Монитор подарков запущен!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    init_db()
    # Запуск бота в отдельном потоке, чтобы он не мешал сайту
    import threading
    threading.Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()
    
    # Порт для Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
