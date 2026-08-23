"""שליפת סטטיסטיקת שחקנים מכל ההיסטוריה של היורוליג, עונה-עונה, בכל קטגוריות
הסטטיסטיקה שה-API מציע.

חשוב: אנחנו עוברים עונה-עונה בעצמנו ומתייגים כל שורה עם העונה שאנחנו כבר
יודעים (כי אנחנו זה שביקשנו אותה) - ולא מנסים לחלץ "עונה" מהתשובה של ה-API.
ניסיון קודם להשתמש בפונקציית "כל העונות" של הספרייה נכשל כי היא מחזירה
שורה אחת מצטברת לכל שחקן על פני כל הקריירה שלו, בלי פירוט לפי עונה.

עמודות הזיהוי הבסיסיות (player.code/player.name/player.team.code/name) כבר
אומתו בפועל מול שרת אמיתי בקטגוריות traditional/advanced/misc. אם קטגוריית
scoring (שלא נבדקה) נכשלת עם שגיאה על "עמודות חסרות", תריץ
`python main.py --debug-columns` ותשלח לי את הפלט.
"""
import datetime

from euroleague_api.player_stats import PlayerStats

import db

CATEGORIES = ["traditional", "advanced", "misc", "scoring"]

# העונה שבה הוקם היורוליג בפורמט הנוכחי שלו (מותג "Euroleague", קוד תחרות E)
FOUNDING_SEASON = 2000

IDENTITY_CANDIDATES = {
    "player_code": ["player.code", "playerCode"],
    "player_name": ["player.name", "playerName"],
    "team_code": ["player.team.code", "player.club.code", "club.code"],
    "team_name": ["player.team.name", "player.club.name", "club.name"],
}

# עמודות שמתעלמים מהן כי הן לא סטטיסטיקה (תמונות, קישורים)
IGNORE_SUBSTRINGS = ["imageUrl", "tvCodes"]

REQUIRED_FIELDS = ["player_code", "player_name"]


def pick(row, field_name):
    for column in IDENTITY_CANDIDATES[field_name]:
        if column in row and row[column] is not None:
            return row[column]
    return None


def first_team_only(value):
    """שחקן שעבר קבוצה באמצע עונה - ה-API לפעמים מחזיר את שתי הקבוצות
    מחוברות במחרוזת אחת עם פסיק-נקודה, למשל 'TEL;PAN'. אנחנו לא מפצלים
    את הסטטיסטיקה בין שתי הקבוצות (לא ניתן לדעת מהתשובה הזו כמה מהמשחקים
    שייכים לכל קבוצה), אז פשוט לוקחים את הראשונה."""
    if value is None:
        return value
    return str(value).split(";")[0].strip()


def current_season_guess() -> int:
    """עונה כמספר השנה שבה היא מתחילה. אם אנחנו לפני אוקטובר, העונה האחרונה
    שרלוונטית היא זו שהתחילה בשנה שעברה."""
    today = datetime.date.today()
    return today.year if today.month >= 10 else today.year - 1


def fetch_category_single_season(category: str, season: int, competition_code: str = "E"):
    """מביא DataFrame גולמי של סטטיסטיקת שחקנים בקטגוריה נתונה, לעונה בודדת."""
    player_stats = PlayerStats(competition_code)
    return player_stats.get_player_stats_single_season(category, season)


def store_category(conn, df, category: str, season_code: str) -> int:
    """שומר DataFrame של עונה+קטגוריה אחת ב-DB. מחזיר כמה שורות שחקנים נשמרו."""
    identity_columns = {c for candidates in IDENTITY_CANDIDATES.values() for c in candidates}

    missing = [f for f in REQUIRED_FIELDS if not any(c in df.columns for c in IDENTITY_CANDIDATES[f])]
    if missing:
        raise RuntimeError(
            f"[{category}/{season_code}] לא נמצאו עמודות מזהות בסיסיות ({missing}). "
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
        if not player_code or not player_name:
            continue

        team_code = first_team_only(pick(row, "team_code"))
        team_name = first_team_only(pick(row, "team_name"))

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


def store_full_history(competition_code: str = "E", start_season: int = FOUNDING_SEASON, end_season: int | None = None):
    """שולף ושומר את כל הקטגוריות, עונה-עונה, מ-start_season ועד end_season.
    עונה שנכשלת (למשל לא קיימת ב-API) מדולגת ולא מפילה את כל הריצה."""
    if end_season is None:
        end_season = current_season_guess()

    conn = db.get_connection()
    db.init_db(conn)

    for category in CATEGORIES:
        total = 0
        seasons_ok = 0
        for season in range(start_season, end_season + 1):
            season_code = f"{competition_code}{season}"
            try:
                df = fetch_category_single_season(category, season, competition_code)
            except Exception as exc:
                print(f"  {season_code}/{category}: דילוג ({exc})")
                continue

            if df is None or df.empty:
                continue

            rows_saved = store_category(conn, df, category, season_code)
            conn.commit()
            total += rows_saved
            seasons_ok += 1

        print(f"{category}: נשמרו {total} רשומות שחקן-עונה, מתוך {seasons_ok} עונות ({start_season}-{end_season})")

    conn.close()
