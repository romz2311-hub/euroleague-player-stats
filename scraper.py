"""שליפת סטטיסטיקת שחקנים מה-API הרשמי של היורוליג ושמירה ב-DB.

הערה חשובה: שמות העמודות המדויקים שמוחזרים מה-API לא אומתו מול שרת אמיתי
(הסביבה שבה נכתב הקוד הזה חוסמת גישה לאינטרנט חיצוני חופשי). לכן יש כאן
רשימת "מועמדים" לכל שדה - אם ריצה ראשונה נכשלת עם שגיאה על עמודה חסרה,
תריץ `python main.py --debug-columns` כדי לראות את שמות העמודות האמיתיים
ותעדכן את ה-CANDIDATES למטה בהתאם.
"""
from euroleague_api.player_stats import PlayerStats

import db

# לכל שדה לוגי - רשימת שמות עמודות אפשריים, לפי סדר עדיפות.
CANDIDATES = {
    "player_code": ["player.code", "playerCode", "player.playerCode"],
    "player_name": ["player.name", "playerName"],
    "country_code": ["player.country.code", "player.countryCode"],
    "country_name": ["player.country.name", "player.countryName"],
    "team_code": ["player.team.code", "player.club.code", "club.code", "teamCode"],
    "team_name": ["player.team.name", "player.club.name", "club.name", "teamName"],
    "games_played": ["gamesPlayed"],
    "games_started": ["gamesStarted"],
    "minutes_played": ["timePlayed", "minutesPlayed"],
    "points": ["pointsScored", "points"],
    "two_pt_made": ["twoPointersMade"],
    "two_pt_attempted": ["twoPointersAttempted"],
    "three_pt_made": ["threePointersMade"],
    "three_pt_attempted": ["threePointersAttempted"],
    "ft_made": ["freeThrowsMade"],
    "ft_attempted": ["freeThrowsAttempted"],
    "offensive_rebounds": ["offensiveRebounds"],
    "defensive_rebounds": ["defensiveRebounds"],
    "total_rebounds": ["totalRebounds"],
    "assists": ["assistances", "assists"],
    "steals": ["steals"],
    "turnovers": ["turnovers"],
    "blocks_favour": ["blocks", "blocksFavour"],
    "blocks_against": ["blocksAgainst"],
    "fouls_committed": ["foulsCommited", "foulsCommitted"],
    "fouls_received": ["foulsDrawn", "foulsReceived"],
    "pir": ["valuation", "pir", "PIR"],
}

REQUIRED_FIELDS = ["player_code", "player_name"]


def pick(row, field_name):
    for column in CANDIDATES[field_name]:
        if column in row and row[column] is not None:
            return row[column]
    return None


def fetch_season_stats(season: int, competition_code: str = "E"):
    """מביא DataFrame גולמי של סטטיסטיקת שחקנים לעונה נתונה."""
    player_stats = PlayerStats(competition_code)
    return player_stats.get_player_stats_single_season("traditional", season)


def store_season_stats(season: int, competition_code: str = "E", conn=None):
    """שולף סטטיסטיקה לעונה ושומר ב-DB (players, teams, player_season_stats)."""
    own_connection = conn is None
    if own_connection:
        conn = db.get_connection()
        db.init_db(conn)

    df = fetch_season_stats(season, competition_code)
    season_code = f"{competition_code}{season}"

    missing = [f for f in REQUIRED_FIELDS if not any(c in df.columns for c in CANDIDATES[f])]
    if missing:
        raise RuntimeError(
            f"לא נמצאו עמודות מזהות בסיסיות ({missing}) בתשובת ה-API. "
            f"עמודות שכן קיימות: {list(df.columns)}. "
            "צריך לעדכן את CANDIDATES ב-scraper.py לפי השמות האמיתיים."
        )

    rows_saved = 0
    for _, row in df.iterrows():
        player_code = pick(row, "player_code")
        player_name = pick(row, "player_name")
        if not player_code or not player_name:
            continue

        country_code = pick(row, "country_code")
        country_name = pick(row, "country_name")
        team_code = pick(row, "team_code")
        team_name = pick(row, "team_name")

        db.upsert_player(conn, player_code, player_name, country_code, country_name)
        if team_code:
            db.upsert_team(conn, team_code, team_name or team_code)

        stats = {
            field: (pick(row, field) or 0)
            for field in CANDIDATES
            if field not in ("player_code", "player_name", "country_code", "country_name", "team_code", "team_name")
        }
        db.upsert_player_season_stats(conn, player_code, season_code, team_code, stats)
        rows_saved += 1

    conn.commit()
    if own_connection:
        conn.close()
    return rows_saved
