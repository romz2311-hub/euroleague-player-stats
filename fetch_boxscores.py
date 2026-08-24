"""שולף סטטיסטיקת שחקנים לפי משחק בודד (box score), עונה-עונה, ומשלים
שחקנים שחסרים מהדוחות העונתיים הרגילים (player_stats) - כי כל שחקן ברשימת
המשחק מקבל שורה, גם אם לא שיחק בו בכלל (Minutes: DNP).

חשוב: הפונקציה של החבילה ל-boxscore בודד לא עושה ניסיון חוזר אוטומטי כשהיא
נחסמת (HTTP 429) - היא פשוט מדלגת ורושמת שגיאה בלוג בלי לדווח לנו. בגלל זה
יש כאן השהיה בין בקשות, ואם תוצאה חוזרת ריקה - ניסיון חוזר אחד אחרי המתנה
(יכול להיות גם משחק שבאמת לא קיים, אז לא מנסים יותר מפעם אחת נוספת).

משחק שכבר נשמר ב-DB לא נשלף שוב (תוצאות משחק שהסתיים לא משתנות) - זה הופך
הרצות חוזרות (כמו update_all.py) למהירות בהרבה אחרי הריצה הראשונה הכבדה.

שימוש:
    python fetch_boxscores.py                    # רק העונה הנוכחית
    python fetch_boxscores.py --season 2024
    python fetch_boxscores.py --start-season 2020 --end-season 2025
"""
import argparse
import time

from euroleague_api.boxscore_data import BoxScoreData

import db
import scraper

REQUEST_DELAY_SECONDS = 1.2
EMPTY_RESULT_BACKOFF_SECONDS = 8
MAX_GAMECODE = 450

STAT_COLUMNS = {
    "TotalRebounds": "total_rebounds",
    "Assistances": "assists",
    "Steals": "steals",
    "Turnovers": "turnovers",
    "BlocksFavour": "blocks_favour",
    "BlocksAgainst": "blocks_against",
    "FoulsCommited": "fouls_committed",
    "FoulsReceived": "fouls_received",
    "Valuation": "valuation",
    "Points": "points",
}


def safe_int(value, default=0):
    try:
        if value is None or value != value:  # value != value מזהה NaN
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def game_already_stored(conn, season_code: str, gamecode: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM player_game_stats WHERE season_code = ? AND game_code = ? LIMIT 1",
        (season_code, gamecode),
    ).fetchone() is not None


def try_fetch(boxscore: BoxScoreData, season: int, gamecode: int):
    """מנסה להביא boxscore למשחק בודד. מחזיר None אם המשחק לא קיים או שהתקבלה
    שגיאה (כולל 429 עם גוף תשובה ריק, שגורם לקוד של החבילה לקרוס על JSON ריק
    אם לא תופסים את זה כאן)."""
    try:
        return boxscore.get_players_boxscore_stats(season, gamecode)
    except Exception:
        return None


def fetch_game(boxscore: BoxScoreData, season: int, gamecode: int):
    df = try_fetch(boxscore, season, gamecode)
    if df is None or df.empty:
        time.sleep(EMPTY_RESULT_BACKOFF_SECONDS)
        df = try_fetch(boxscore, season, gamecode)
    return df


def store_game(conn, df, season_code: str) -> int:
    if df is None or df.empty:
        return 0

    saved = 0
    for _, row in df.iterrows():
        player_code = row.get("Player_ID")
        player_name = row.get("Player")
        if not player_code or not player_name:
            continue

        team_code = row.get("Team")
        db.upsert_player(conn, player_code, player_name)
        if team_code and not conn.execute("SELECT 1 FROM teams WHERE team_code = ?", (team_code,)).fetchone():
            db.upsert_team(conn, team_code, team_code)

        stats = {}
        for source_col, db_col in STAT_COLUMNS.items():
            value = row.get(source_col)
            if value is not None and value == value:  # not NaN
                stats[db_col] = value

        minutes = row.get("Minutes")
        # שדה ה-IsPlaying שמגיע מה-API לא אמין (שחקן עם דקות משחק בפועל
        # מסומן שם לפעמים כ-0) - קובעים בעצמנו לפי שדה הדקות במקום.
        did_play = 1 if minutes and str(minutes).strip().upper() != "DNP" else 0

        db.upsert_game_stat(
            conn,
            player_code=player_code,
            season_code=season_code,
            game_code=safe_int(row.get("Gamecode")),
            round_number=safe_int(row.get("Round"), default=None),
            team_code=team_code,
            is_starter=safe_int(row.get("IsStarter")),
            is_playing=did_play,
            minutes=minutes,
            stats=stats,
        )
        saved += 1

    return saved


def store_season_boxscores(season: int, competition_code: str = "E", max_gamecode: int = MAX_GAMECODE):
    conn = db.get_connection()
    db.init_db(conn)

    season_code = f"{competition_code}{season}"
    boxscore = BoxScoreData(competition_code)

    games_with_data = 0
    games_skipped_cached = 0
    total_rows = 0

    for gamecode in range(1, max_gamecode + 1):
        if game_already_stored(conn, season_code, gamecode):
            games_skipped_cached += 1
            continue

        df = fetch_game(boxscore, season, gamecode)
        rows_saved = store_game(conn, df, season_code)
        if rows_saved:
            games_with_data += 1
            total_rows += rows_saved

        if gamecode % 20 == 0:
            conn.commit()
            print(f"  {season_code}: נבדקו {gamecode}/{max_gamecode}, {games_with_data} חדשים עם נתונים, "
                  f"{games_skipped_cached} כבר היו שמורים, {total_rows} רשומות שחקן-משחק חדשות")

        time.sleep(REQUEST_DELAY_SECONDS)

    conn.commit()
    conn.close()
    print(f"{season_code}: סיום. {games_with_data} משחקים חדשים, {games_skipped_cached} כבר היו שמורים, "
          f"{total_rows} רשומות שחקן-משחק חדשות")


def main():
    parser = argparse.ArgumentParser(description="Fetch per-game boxscore stats")
    default_season = scraper.current_season_guess()
    parser.add_argument("--season", type=int, default=None, help="עונה בודדת")
    parser.add_argument("--start-season", type=int, default=default_season)
    parser.add_argument("--end-season", type=int, default=default_season)
    parser.add_argument("--competition", default="E", choices=["E", "U"])
    args = parser.parse_args()

    seasons = [args.season] if args.season is not None else range(args.start_season, args.end_season + 1)
    for season in seasons:
        store_season_boxscores(season, args.competition)


if __name__ == "__main__":
    main()
