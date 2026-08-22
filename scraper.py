"""שליפת סטטיסטיקת שחקנים מכל ההיסטוריה של היורוליג (כל העונות שה-API מכיר),
בכל קטגוריות הסטטיסטיקה שה-API מציע.

הערה חשובה: כמו בגרסה הקודמת של הפרויקט, לא הצלחתי לבדוק שמות עמודות מדויקים
מול שרת אמיתי מהסביבה שבה נכתב הקוד (חסומה גישה חיצונית). עמודות הזיהוי
הבסיסיות (player_code/player_name/team) כבר אומתו בפועל ב-traditional. אם
קטגוריה אחרת (advanced/misc/scoring) נכשלת עם שגיאה על "עמודות חסרות", תריץ
`python main.py --debug-columns` ותשלח לי את הפלט.
"""
from euroleague_api.player_stats import PlayerStats

import db

CATEGORIES = ["traditional", "advanced", "misc", "scoring"]

IDENTITY_CANDIDATES = {
    "player_code": ["player.code", "playerCode"],
    "player_name": ["player.name", "playerName"],
    "team_code": ["player.team.code", "player.club.code", "club.code"],
    "team_name": ["player.team.name", "player.club.name", "club.name"],
    "season_code": ["seasonCode", "SeasonCode", "season", "Season", "player.seasonCode"],
}

# עמודות שמתעלמים מהן כי הן לא סטטיסטיקה (תמונות, קישורים)
IGNORE_SUBSTRINGS = ["imageUrl", "tvCodes"]

REQUIRED_FIELDS = ["player_code", "player_name", "season_code"]


def pick(row, field_name):
    for column in IDENTITY_CANDIDATES[field_name]:
        if column in row and row[column] is not None:
            return row[column]
    return None


def fetch_category_all_seasons(category: str, competition_code: str = "E"):
    """מביא DataFrame גולמי של סטטיסטיקת שחקנים בקטגוריה נתונה, לכל העונות."""
    player_stats = PlayerStats(competition_code)
    return player_stats.get_player_stats_all_seasons(category)


def store_category(conn, df, category: str) -> int:
    """שומר DataFrame של קטגוריה אחת ב-DB. מחזיר כמה שורות (player-season) נשמרו."""
    identity_columns = {c for candidates in IDENTITY_CANDIDATES.values() for c in candidates}

    missing = [f for f in REQUIRED_FIELDS if not any(c in df.columns for c in IDENTITY_CANDIDATES[f])]
    if missing:
        raise RuntimeError(
            f"[{category}] לא נמצאו עמודות מזהות בסיסיות ({missing}). "
            f"עמודות קיימות: {list(df.columns)}. "
            "צריך לעדכן את IDENTITY_CANDIDATES ב-scraper.py."
        )

    stat_columns = [
        c for c in df.columns
        if c not in identity_columns and not any(s in c for s in IGNORE_SUBSTRINGS)
    ]

    rows_saved = 0
    for _, row in df.iterrows():
        player_code = pick(row, "player_code")
        player_name = pick(row, "player_name")
        season_code = pick(row, "season_code")
        if not player_code or not player_name or not season_code:
            continue

        team_code = pick(row, "team_code")
        team_name = pick(row, "team_name")

        db.upsert_player(conn, player_code, player_name)
        if team_code:
            db.upsert_team(conn, team_code, team_name or team_code)

        for stat_name in stat_columns:
            value = row[stat_name]
            if value is None or value != value:  # value != value מזהה NaN
                continue
            db.upsert_stat(conn, player_code, season_code, team_code, category, stat_name, value)

        rows_saved += 1

    return rows_saved


def store_full_history(competition_code: str = "E"):
    """שולף ושומר את כל הקטגוריות, לכל העונות. מדפיס התקדמות."""
    conn = db.get_connection()
    db.init_db(conn)

    for category in CATEGORIES:
        df = fetch_category_all_seasons(category, competition_code)
        rows_saved = store_category(conn, df, category)
        conn.commit()
        print(f"{category}: נשמרו {rows_saved} רשומות (שחקן-עונה)")

    conn.close()
