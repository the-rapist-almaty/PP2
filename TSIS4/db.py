"""
db.py — PostgreSQL helpers for Snake leaderboard.
Tables: players, game_sessions
"""

import psycopg2
from config import DB_CONFIG


def _conn():
    return psycopg2.connect(**DB_CONFIG)


# Schema

def ensure_tables():
    """Create tables if they don't exist yet."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER   NOT NULL,
                    level_reached INTEGER   NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)


#  Players 

def get_or_create_player(username: str) -> int:
    """Return player id, creating the row if needed."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) RETURNING id;",
                (username,)
            )
            return cur.fetchone()[0]


#  Sessions 

def save_session(username: str, score: int, level: int):
    """Insert a game result for the given player."""
    pid = get_or_create_player(username)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) "
                "VALUES (%s, %s, %s);",
                (pid, score, level)
            )


def get_top10():
    """Return top-10 all-time scores."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached,
                       gs.played_at::date
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT 10;
            """)
            return cur.fetchall()


def get_personal_best(username: str) -> int:
    """Return the highest score for this player (0 if none)."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(MAX(gs.score), 0)
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                WHERE p.username = %s;
            """, (username,))
            return cur.fetchone()[0]
