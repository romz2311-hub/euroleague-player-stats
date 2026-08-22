"""נקודת כניסה: שליפת סטטיסטיקת שחקני יורוליג לכל ההיסטוריה, בכל קטגוריות
הסטטיסטיקה, ושמירה למסד נתונים מקומי.

שימוש:
    python main.py                      # שולף הכל: כל העונות, כל הקטגוריות (traditional/advanced/misc/scoring)
    python main.py --competition U      # יורוקאפ במקום יורוליג
    python main.py --debug-columns      # רק להציג את שמות העמודות מכל קטגוריה, בלי לשמור כלום ב-DB
"""
import argparse

import scraper


def main():
    parser = argparse.ArgumentParser(description="Euroleague full-history player stats scraper")
    parser.add_argument("--competition", default="E", choices=["E", "U"], help="E=יורוליג, U=יורוקאפ")
    parser.add_argument(
        "--debug-columns",
        action="store_true",
        help="מציג את שמות העמודות שחוזרות מה-API בכל קטגוריה, בלי לשמור כלום ב-DB",
    )
    args = parser.parse_args()

    if args.debug_columns:
        category = "traditional"
        df = scraper.fetch_category_all_seasons(category, args.competition)
        print(f"--- {category}: columns ---")
        print(list(df.columns))
        print(f"\n--- {category}: index name(s) ---")
        print(df.index.names)
        print(f"\n--- {category}: shape ---")
        print(df.shape)
        print(f"\n--- {category}: first 2 rows (all columns) ---")
        print(df.head(2).to_string())
        return

    scraper.store_full_history(args.competition)
    print("סיום. כל ההיסטוריה נשמרה ב-data/euroleague.db")


if __name__ == "__main__":
    main()
