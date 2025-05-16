import socket
import threading
import json
import hashlib
import secrets
import datetime
from pathlib import Path
import os  # добавлено для работы с переменными окружения

HOST = '0.0.0.0'  # слушать все интерфейсы

# Получаем порт из переменной окружения PORT, если нет — ставим 10000
PORT = int(os.environ.get("PORT", 10000))

DATA_DIR = Path("data")
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
CHAT_FILE = DATA_DIR / "chat.json"

clients = []
lock = threading.Lock()

def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        ACCOUNTS_FILE.write_text(json.dumps({"users": []}, ensure_ascii=False, indent=2))
    if not CHAT_FILE.exists():
        CHAT_FILE.write_text(json.dumps({"messages": []}, ensure_ascii=False, indent=2))

# остальной код без изменений...

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def register_user(username, password):
    accounts = load_json(ACCOUNTS_FILE)
    if any(u['username'] == username for u in accounts['users']):
        return {"status": "error", "message": "Пользователь уже существует."}
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    accounts['users'].append({"username": username, "salt": salt, "password_hash": password_hash})
    save_json(ACCOUNTS_FILE, accounts)
    return {"status": "ok"}

def login_user(username, password):
    accounts = load_json(ACCOUNTS_FILE)
    for user in accounts['users']:
        if user['username'] == username:
            if hash_password(password, user['salt']) == user['password_hash']:
                return {"status": "ok"}
            else:
                return {"status": "error", "message": "Неверный пароль."}
    return {"status": "error", "message": "Пользователь не найден."}

def add_message(username, text):
    chat = load_json(CHAT_FILE)
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    chat['messages'].append({"username": username, "timestamp": timestamp, "text": text})
    save_json(CHAT_FILE, chat)

def handle_client(conn, addr):
    print(f"[+] Подключен клиент: {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break
                request = json.loads(data)
                response = {}

                if request["action"] == "register":
                    response = register_user(request["username"], request["password"])
                elif request["action"] == "login":
                    response = login_user(request["username"], request["password"])
                elif request["action"] == "send_message":
                    add_message(request["username"], request["text"])
                    response = {"status": "ok"}
                elif request["action"] == "get_messages":
                    chat = load_json(CHAT_FILE)
                    response = {"status": "ok", "messages": chat['messages']}
                else:
                    response = {"status": "error", "message": "Неизвестное действие."}

                conn.sendall(json.dumps(response).encode("utf-8"))
            except Exception as e:
                print(f"[!] Ошибка с клиентом {addr}: {e}")
                break
    print(f"[-] Отключен клиент: {addr}")

def start_server():
    ensure_data_files()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER] Сервер запущен на {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()

if __name__ == "__main__":
    start_server()
