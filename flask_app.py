import json
import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request, abort

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "data.json"
SYNC_TOKEN = os.environ.get("SYNC_TOKEN", "respect-games-sync-key")

DEFAULT_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png"
BOT_AVATAR = "https://cdn.discordapp.com/avatars/1364045768854999150/a_853d7d3fa3e1b20c09f1a055a0e2a0cc.webp"
BOT_INVITE = "https://discord.com/oauth2/authorize?client_id=1364045768854999150"
WHEEL_URL = "https://draks518.github.io/respect-wheel/"


def load_data() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text("utf-8"))
    return {"guild_name": "Respect Community", "guild_id": 0, "users": {}}


def get_user_list(data: dict) -> list[dict]:
    users = []
    for uid, entry in data.get("users", {}).items():
        if isinstance(entry, int):
            users.append({"id": int(uid), "points": entry, "name": None, "avatar": None})
        else:
            users.append({"id": int(uid), "points": entry.get("points", 0), "name": entry.get("name"), "avatar": entry.get("avatar")})
    users.sort(key=lambda x: x["points"], reverse=True)
    return users


@app.route("/")
def index():
    data = load_data()
    users = get_user_list(data)
    total_players = len(users)
    total_points = sum(u["points"] for u in users)
    return render_template("index.html",
                           server_name=data.get("guild_name", "Respect Community"),
                           bot_invite=BOT_INVITE,
                           wheel_url=WHEEL_URL,
                           bot_avatar=BOT_AVATAR,
                           default_avatar=DEFAULT_AVATAR,
                           total_players=total_players,
                           total_points=total_points,
                           top=users[:5])


@app.route("/leaderboard")
def leaderboard():
    data = load_data()
    users = get_user_list(data)
    total_players = len(users)
    total_points = sum(u["points"] for u in users)
    query = request.args.get("q", "").strip().lower()
    if query:
        users = [u for u in users if u.get("name") and query in u["name"].lower()]
    return render_template("leaderboard.html",
                           server_name=data.get("guild_name", "Respect Community"),
                           bot_invite=BOT_INVITE,
                           bot_avatar=BOT_AVATAR,
                           default_avatar=DEFAULT_AVATAR,
                           total_players=total_players,
                           total_points=total_points,
                           top=users,
                           query=query)


@app.route("/api/data")
def api_data():
    return jsonify(load_data())


@app.route("/api/sync", methods=["POST"])
def api_sync():
    token = request.headers.get("X-Sync-Token", "")
    if token != SYNC_TOKEN:
        abort(401, "Invalid token")
    payload = request.get_json()
    if not payload or "users" not in payload:
        abort(400, "Invalid data")
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"status": "ok"})
