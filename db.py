"""שכבת גישה למסד הנתונים (SQLite).

המבנה מנורמל לשלוש טבלאות: שחקנים, קבוצות, וסטטיסטיקה לפי עונה.
כך אפשר לשלוף סטטיסטיקה גם לפי מדינה וגם לפי קבוצה בלי לשכפל נתונים.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "euroleague.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    player_code TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    country_code TEXT,
    country_name TEXT
);

CREATE TABLE IF NOT EXISTS teams (
    team_code TEXT PRIMARY KEY,
    team_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS player_season_stats (
    player_code TEXT NOT NULL,
    season_code TEXT NOT NULL,
    team_code TEXT,
    games_played INTEGER,
    games_started INTEGER,
    minutes_played REAL,
    points REAL,
    two_pt_made REAL,
    two_pt_attempted REAL,
    three_pt_made REAL,
    three_pt_attempted REAL,
    ft_made REAL,
    ft_attempted REAL,
    offensive_rebounds REAL,
    defensive_rebounds REAL,
    total_rebounds REAL,
    assists REAL,
    steals REAL,
    turnovers REAL,
    blocks_favour REAL,
    blocks_against REAL,
    fouls_committed REAL,
    fouls_received REAL,
    pir REAL,
    PRIMARY KEY (player_code, season_code),
    FOREIGN KEY (player_code) REFERENCES players(player_code),
    FOREIGN KEY (team_code) REFERENCES teams(team_code)
);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_player(conn, player_code, full_name, country_code, country_name):
    conn.execute(
        """
        INSERT INTO players (player_code, full_name, country_code, country_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(player_code) DO UPDATE SET
            full_name = excluded.full_name,
            country_code = excluded.country_code,
            country_name = excluded.country_name
        """,
        (player_code, full_name, country_code, country_name),
    )


def upsert_team(conn, team_code, team_name):
    conn.execute(
        """
        INSERT INTO teams (team_code, team_name)
        VALUES (?, ?)
        ON CONFLICT(team_code) DO UPDATE SET team_name = excluded.team_name
        """,
        (team_code, team_name),
    )


def upsert_player_season_stats(conn, player_code, season_code, team_code, stats: dict):
    columns = ["player_code", "season_code", "team_code"] + list(stats.keys())
    placeholders = ", ".join(["?"] * len(columns))
    updates = ", ".join(f"{c} = excluded.{c}" for c in stats.keys())
    values = [player_code, season_code, team_code] + list(stats.values())
    conn.execute(
        f"""
        INSERT INTO player_season_stats ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(player_code, season_code) DO UPDATE SET {updates}
        """,
        values,
    )


def stats_by_country(conn, country_name: str, season_code: str | None = None):
    query = """
        SELECT p.full_name, p.country_name, s.team_code, s.*
        FROM player_season_stats s
        JOIN players p ON p.player_code = s.player_code
        WHERE p.country_name = ?
    """
    params = [country_name]
    if season_code:
        query += " AND s.season_code = ?"
        params.append(season_code)
    return conn.execute(query, params).fetchall()


def stats_by_team(conn, team_code: str, season_code: str | None = None):
    query = """
        SELECT p.full_name, p.country_name, s.team_code, s.*
        FROM player_season_stats s
        JOIN players p ON p.player_code = s.player_code
        WHERE s.team_code = ?
    """
    params = [team_code]
    if season_code:
        query += " AND s.season_code = ?"
        params.append(season_code)
    return conn.execute(query, params).fetchall()
