from flask import Flask, request, jsonify
import json, hashlib, secrets, datetime
from pathlib import Path

app = Flask(__name__)
DATA_DIR = Path("data")
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
CHAT_FILE = DATA_DIR / "chat.json"

def init_storage():
    DATA_DIR.mkdir(exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        ACCOUNTS_FILE.write_text(json.dumps({"users": []}, indent=2))
    if not CHAT_FILE.exists():
        CHAT_FILE.write_text(json.dumps({"messages": []}, indent=2))

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def save(path, data): path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    accounts = load(ACCOUNTS_FILE)
    if any(u["username"] == data["username"] for u in accounts["users"]):
        return jsonify({"status": "error", "message": "Пользователь уже существует."})
    salt = secrets.token_hex(8)
    password_hash = hash_password(data["password"], salt)
    accounts["users"].append({
        "username": data["username"],
        "salt": salt,
        "password_hash": password_hash
    })
    save(ACCOUNTS_FILE, accounts)
    return jsonify({"status": "ok"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    accounts = load(ACCOUNTS_FILE)
    for u in accounts["users"]:
        if u["username"] == data["username"]:
            if hash_password(data["password"], u["salt"]) == u["password_hash"]:
                return jsonify({"status": "ok"})
            return jsonify({"status": "error", "message": "Неверный пароль."})
    return jsonify({"status": "error", "message": "Пользователь не найден."})

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    chat = load(CHAT_FILE)
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    chat["messages"].append({
        "username": data["username"],
        "timestamp": timestamp,
        "text": data["text"]
    })
    save(CHAT_FILE, chat)
    return jsonify({"status": "ok"})

@app.route("/messages", methods=["GET"])
def get_messages():
    chat = load(CHAT_FILE)
    return jsonify({"status": "ok", "messages": chat["messages"]})

if __name__ == "__main__":
    init_storage()
    app.run(host="0.0.0.0", port=10000)
