from flask import Flask, request, jsonify
import json
import hashlib
import secrets
import datetime
from pathlib import Path
import os

app = Flask(__name__)

DATA_DIR = Path("data")
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
CHAT_FILE = DATA_DIR / "chat.json"

def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        ACCOUNTS_FILE.write_text(json.dumps({"users": []}, ensure_ascii=False, indent=2))
    if not CHAT_FILE.exists():
        CHAT_FILE.write_text(json.dumps({"messages": []}, ensure_ascii=False, indent=2))

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"status": "error", "message": "Имя пользователя и пароль обязательны."}), 400

    accounts = load_json(ACCOUNTS_FILE)
    if any(u['username'] == username for u in accounts['users']):
        return jsonify({"status": "error", "message": "Пользователь уже существует."})

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    accounts['users'].append({"username": username, "salt": salt, "password_hash": password_hash})
    save_json(ACCOUNTS_FILE, accounts)
    return jsonify({"status": "ok", "message": "Регистрация прошла успешно."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"status": "error", "message": "Имя пользователя и пароль обязательны."}), 400

    accounts = load_json(ACCOUNTS_FILE)
    for user in accounts['users']:
        if user['username'] == username:
            if hash_password(password, user['salt']) == user['password_hash']:
                return jsonify({"status": "ok", "message": "Вход выполнен успешно."})
            else:
                return jsonify({"status": "error", "message": "Неверный пароль."})
    return jsonify({"status": "error", "message": "Пользователь не найден."})

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    username = data.get("username")
    text = data.get("text")
    if not username or not text:
        return jsonify({"status": "error", "message": "Параметры username и text обязательны."}), 400

    chat = load_json(CHAT_FILE)
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    chat['messages'].append({"username": username, "timestamp": timestamp, "text": text})
    save_json(CHAT_FILE, chat)
    return jsonify({"status": "ok", "message": "Сообщение отправлено."})

@app.route("/messages", methods=["GET"])
def get_messages():
    chat = load_json(CHAT_FILE)
    return jsonify({"status": "ok", "messages": chat['messages']})

if __name__ == "__main__":
    ensure_data_files()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
