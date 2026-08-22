"""שכבת גישה למסד הנתונים (SQLite).

מבנה: players + teams (טבלאות זהות), ו-player_stats שמחזיקה כל סטטיסטיקה
כשורה נפרדת (player, season, category, stat_name, stat_value) במקום עמודה
קבועה לכל סוג סטטיסטיקה. זה מאפשר לתמוך בכמה קטגוריות סטטיסטיקה שונות
(traditional/advanced/misc/scoring) בלי לדעת מראש את כל שמות העמודות שלהן.
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

CREATE TABLE IF NOT EXISTS player_stats (
    player_code TEXT NOT NULL,
    season_code TEXT NOT NULL,
    team_code TEXT,
    category TEXT NOT NULL,
    stat_name TEXT NOT NULL,
    stat_value REAL,
    PRIMARY KEY (player_code, season_code, category, stat_name),
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
    # מבנה ה-DB מהגרסה הקודמת (עונה בודדת, עמודות קבועות) התחלף לגמרי.
    conn.execute("DROP TABLE IF EXISTS player_season_stats")
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_player(conn, player_code, full_name, country_code=None, country_name=None):
    conn.execute(
        """
        INSERT INTO players (player_code, full_name, country_code, country_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(player_code) DO UPDATE SET
            full_name = excluded.full_name,
            country_code = COALESCE(excluded.country_code, players.country_code),
            country_name = COALESCE(excluded.country_name, players.country_name)
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


def upsert_stat(conn, player_code, season_code, team_code, category, stat_name, stat_value):
    conn.execute(
        """
        INSERT INTO player_stats (player_code, season_code, team_code, category, stat_name, stat_value)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_code, season_code, category, stat_name) DO UPDATE SET
            team_code = excluded.team_code,
            stat_value = excluded.stat_value
        """,
        (player_code, season_code, team_code, category, stat_name, stat_value),
    )


def query_stats(conn, category: str | None = None, team_code: str | None = None, country_name: str | None = None):
    """שליפה גמישה: לפי קטגוריה/קבוצה/מדינה (כל פרמטר אופציונלי), מסודר כרונולוגית."""
    query = """
        SELECT p.full_name, p.country_name, s.team_code, s.season_code, s.category, s.stat_name, s.stat_value
        FROM player_stats s
        JOIN players p ON p.player_code = s.player_code
        WHERE 1=1
    """
    params = []
    if category:
        query += " AND s.category = ?"
        params.append(category)
    if team_code:
        query += " AND s.team_code = ?"
        params.append(team_code)
    if country_name:
        query += " AND p.country_name = ?"
        params.append(country_name)
    query += " ORDER BY s.season_code, p.full_name"
    return conn.execute(query, params).fetchall()


def career_averages(
    conn,
    category: str = "traditional",
    stat_name: str = "pointsScored",
    min_games: int = 100,
    country_name: str | None = None,
):
    """ממוצע קריירה לכל שחקן, על פני כל העונות שנשמרו ב-DB - משוקלל לפי מספר
    המשחקים בכל עונה (לא ממוצע פשוט של הממוצעים העונתיים, כדי שעונה עם מעט
    משחקים לא תשפיע באותו משקל כמו עונה מלאה). אפשר לסנן למדינה ספציפית."""
    query = """
        SELECT p.full_name, p.country_name,
               SUM(s.stat_value * g.stat_value) * 1.0 / SUM(g.stat_value) AS career_avg,
               SUM(g.stat_value) AS total_games,
               COUNT(DISTINCT s.season_code) AS seasons
        FROM player_stats s
        JOIN player_stats g
            ON g.player_code = s.player_code
           AND g.season_code = s.season_code
           AND g.category = s.category
           AND g.stat_name = 'gamesPlayed'
        JOIN players p ON p.player_code = s.player_code
        WHERE s.category = ? AND s.stat_name = ?
    """
    params = [category, stat_name]
    if country_name:
        query += " AND p.country_name = ?"
        params.append(country_name)
    query += " GROUP BY s.player_code HAVING SUM(g.stat_value) >= ? ORDER BY career_avg DESC"
    params.append(min_games)
    return conn.execute(query, params).fetchall()


def countries_summary(conn):
    """כמה שחקנים (עם מדינה ידועה) יש לכל מדינה ב-DB, מהגבוה לנמוך."""
    return conn.execute(
        """
        SELECT country_name, COUNT(*) AS players
        FROM players
        WHERE country_name IS NOT NULL
        GROUP BY country_name
        ORDER BY players DESC
        """
    ).fetchall()
