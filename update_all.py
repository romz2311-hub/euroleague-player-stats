"""מריץ את כל התהליך בפעם אחת: מרענן את העונה הנוכחית (סטטיסטיקה + סגלים
רשמיים + מדינות לשחקנים חדשים + box-score למשחקים חדשים) ובונה מחדש את
הדשבורד. לא נוגע בעונות ישנות (אלה לא משתנות) - רק בעונה הנוכחית, כדי שזה
יהיה מהיר ולא יעמיס מיותר על ה-API. שלב ה-box-score מדלג על משחקים שכבר
נשמרו, אז אחרי הריצה הראשונה (הכבדה) הריצות הבאות מהירות בהרבה.

מיועד להרצה אוטומטית מתוזמנת (למשל דרך Windows Task Scheduler, ראה
run_update.bat) כדי שהדשבורד יישאר מעודכן בלי הרצה ידנית של כל שלב.

שימוש:
    python update_all.py
"""
import datetime

import build_dashboard
import fetch_boxscores
import fetch_countries
import fetch_rosters
import scraper


def main():
    started = datetime.datetime.now()
    print(f"=== התחלת עדכון: {started.isoformat(timespec='seconds')} ===\n")

    current_season = scraper.current_season_guess()

    print(f"--- שלב 1/5: סטטיסטיקת שחקנים לעונה {current_season} ---")
    scraper.store_full_history(start_season=current_season, end_season=current_season)

    print("\n--- שלב 2/5: סגלים רשמיים (עונה נוכחית) ---")
    fetch_rosters.main()

    print("\n--- שלב 3/5: מדינות לשחקנים חדשים ---")
    fetch_countries.main()

    print("\n--- שלב 4/5: box-score למשחקים חדשים ---")
    fetch_boxscores.store_season_boxscores(current_season)

    print("\n--- שלב 5/5: בניית דשבורד ---")
    build_dashboard.main()

    finished = datetime.datetime.now()
    print(f"\n=== עדכון הסתיים: {finished.isoformat(timespec='seconds')} (משך: {finished - started}) ===")


if __name__ == "__main__":
    main()
