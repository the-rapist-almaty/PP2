"""
persistence.py — Save/load leaderboard and settings to JSON files.
"""

import json
import os
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

# ── Default settings ───────────────────────────────────────────
DEFAULT_SETTINGS = {
    "sound":      False,
    "car_color":  [50, 180, 255],
    "difficulty": "normal"   # "easy" | "normal" | "hard"
}


# ══════════════════════════════════════════════════════════════
#  LEADERBOARD
# ══════════════════════════════════════════════════════════════

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_score(username: str, score: int, distance: int, coins: int):
    board = load_leaderboard()
    board.append({
        "username": username,
        "score":    score,
        "distance": distance,
        "coins":    coins,
        "date":     datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    # Keep top 10 sorted by score
    board.sort(key=lambda x: x["score"], reverse=True)
    board = board[:10]
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    # Fill missing keys with defaults
    for k, v in DEFAULT_SETTINGS.items():
        data.setdefault(k, v)
    return data


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
