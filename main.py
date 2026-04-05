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
SESSION_PATH = 'bank_account'

app = Flask(__name__)
client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

# База данных
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, status TEXT)')
    conn.commit()
    conn.close()

# Мониторинг подарков
@client.on(events.NewMessage)
async def handler(event):
    if event.gift:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO inventory (user_id, status) VALUES (?, ?)", (event.sender_id, 'available'))
        conn.commit()
        conn.close()

# Сайт
@app.route('/')
def index(): return "Server is Running!"

@app.route('/api/my_gifts')
def my_gifts():
    uid = request.args.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    gifts = conn.execute('SELECT * FROM inventory WHERE user_id = ? AND status = "available"', (uid,)).fetchall()
    return jsonify([dict(g) for g in gifts])

# Запуск всего вместе
async def run_bot():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    init_db()
    # Запускаем бота в фоне
    import threading
    threading.Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()
    # Запускаем сайт
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)