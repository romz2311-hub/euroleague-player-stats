"""נקודת כניסה: שליפת סטטיסטיקת שחקני יורוליג לכל ההיסטוריה (עונה-עונה), בכל
קטגוריות הסטטיסטיקה, ושמירה למסד נתונים מקומי.

שימוש:
    python main.py                                # שולף הכל: 2000 ועד היום, כל הקטגוריות
    python main.py --start-season 2015             # רק מ-2015 ואילך (מהיר יותר לבדיקה)
    python main.py --competition U                 # יורוקאפ במקום יורוליג
    python main.py --debug-columns --category scoring --season 2024   # בדיקת עמודות מהירה, בלי לשמור ב-DB
"""
import argparse

import scraper


def main():
    parser = argparse.ArgumentParser(description="Euroleague full-history player stats scraper")
    parser.add_argument("--competition", default="E", choices=["E", "U"], help="E=יורוליג, U=יורוקאפ")
    parser.add_argument("--start-season", type=int, default=scraper.FOUNDING_SEASON, help="עונת התחלה (ברירת מחדל: 2000)")
    parser.add_argument("--end-season", type=int, default=None, help="עונת סיום (ברירת מחדל: העונה הנוכחית)")
    parser.add_argument(
        "--debug-columns",
        action="store_true",
        help="מציג את שמות העמודות בעונה+קטגוריה בודדת, בלי לשמור כלום ב-DB",
    )
    parser.add_argument("--category", default="traditional", choices=scraper.CATEGORIES, help="לשימוש עם --debug-columns")
    parser.add_argument("--season", type=int, default=2024, help="לשימוש עם --debug-columns")
    args = parser.parse_args()

    if args.debug_columns:
        df = scraper.fetch_category_single_season(args.category, args.season, args.competition)
        print(f"--- {args.category} {args.competition}{args.season}: {len(df)} שורות ---")
        print(list(df.columns))
        return

    scraper.store_full_history(args.competition, args.start_season, args.end_season)
    print("סיום. כל ההיסטוריה נשמרה ב-data/euroleague.db")


if __name__ == "__main__":
    main()
