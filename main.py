"""נקודת כניסה: שליפת סטטיסטיקת שחקני יורוליג ושמירה למסד נתונים מקומי.

שימוש:
    python main.py --season 2024
    python main.py --season 2024 --competition U      # יורוקאפ
    python main.py --debug-columns --season 2024       # רק להציג עמודות מה-API, בלי לשמור
"""
import argparse

import scraper


def main():
    parser = argparse.ArgumentParser(description="Euroleague player stats scraper")
    parser.add_argument("--season", type=int, required=True, help="שנת התחלת העונה, למשל 2024")
    parser.add_argument("--competition", default="E", choices=["E", "U"], help="E=יורוליג, U=יורוקאפ")
    parser.add_argument(
        "--debug-columns",
        action="store_true",
        help="מציג את שמות העמודות שחוזרות מה-API בלי לשמור כלום ב-DB",
    )
    args = parser.parse_args()

    if args.debug_columns:
        df = scraper.fetch_season_stats(args.season, args.competition)
        print(list(df.columns))
        return

    rows_saved = scraper.store_season_stats(args.season, args.competition)
    print(f"נשמרו {rows_saved} רשומות שחקנים לעונה {args.competition}{args.season}")


if __name__ == "__main__":
    main()
