"""משלים לטבלת players שחקנים שנמצאים בסגל הרשמי של קבוצה אבל אין להם
עדיין סטטיסטיקה (כי לא שיחקו מספיק דקות) - למשל שחקני הרכב/בית צעירים.
משתמש בנקודת קצה שונה (סגל קבוצה, לא סטטיסטיקה) שכוללת את כל הרשומים,
וגם נותנת מדינה ישירות (בלי צורך ב-fetch_countries.py בשבילם).

ברירת מחדל: רק העונה הנוכחית (כדי לא להעמיס יותר מדי בקשות על השרת).
להרחיב לעונות נוספות: python fetch_rosters.py --start-season 2020

שימוש:
    python fetch_rosters.py
    python fetch_rosters.py --start-season 2020 --end-season 2025
"""
import argparse
import time
from collections import Counter

import requests

import db
import scraper

BASE_URL = "https://api-live.euroleague.net"
REQUEST_DELAY_SECONDS = 1.0
MAX_RETRIES_ON_RATE_LIMIT = 5
BACKOFF_BASE_SECONDS = 5


def fetch_roster(season_code: str, team_code: str, competition_code: str = "E"):
    """מחזיר (members_list, reason_if_failed)."""
    url = f"{BASE_URL}/v2/competitions/{competition_code}/seasons/{season_code}/clubs/{team_code}/people"

    for attempt in range(MAX_RETRIES_ON_RATE_LIMIT + 1):
        response = requests.get(url, timeout=15)

        if response.status_code == 429:
            if attempt == MAX_RETRIES_ON_RATE_LIMIT:
                return None, "HTTP 429 (נכשל גם אחרי כמה ניסיונות המתנה)"
            retry_after = response.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after else BACKOFF_BASE_SECONDS * (attempt + 1)
            time.sleep(wait_seconds)
            continue

        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        body = response.json()
        # ננסה כמה צורות עטיפה אפשריות ל-JSON, לא בטוחים באיזו מהן ה-API משתמש כאן
        if isinstance(body, list):
            return body, None
        if isinstance(body, dict):
            for key in ("data", "rows", "people"):
                if isinstance(body.get(key), list):
                    return body[key], None
            return None, f"200 אבל מבנה JSON לא מוכר: {list(body.keys())}"
        return None, f"200 אבל תשובה לא צפויה: {type(body)}"

    return None, "unreachable"


def main():
    parser = argparse.ArgumentParser(description="Backfill full team rosters, including players with no recorded stats yet")
    default_season = scraper.current_season_guess()
    parser.add_argument("--start-season", type=int, default=default_season, help=f"ברירת מחדל: רק העונה הנוכחית ({default_season})")
    parser.add_argument("--end-season", type=int, default=default_season)
    parser.add_argument("--competition", default="E", choices=["E", "U"])
    args = parser.parse_args()

    conn = db.get_connection()
    all_team_seasons = conn.execute(
        "SELECT DISTINCT season_code, team_code FROM player_stats WHERE team_code IS NOT NULL"
    ).fetchall()

    team_seasons = [
        (season_code, team_code)
        for season_code, team_code in all_team_seasons
        if args.start_season <= int(season_code[len(args.competition):]) <= args.end_season
    ]

    print(f"בודק {len(team_seasons)} צירופי קבוצה-עונה (עונות {args.start_season}-{args.end_season})...")

    added = 0
    failure_reasons = Counter()
    printed_debug_sample = False

    for i, (season_code, team_code) in enumerate(team_seasons, start=1):
        members, reason = fetch_roster(season_code, team_code, args.competition)

        if reason:
            failure_reasons[reason] += 1
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        if not printed_debug_sample:
            print(f"  (דוגמת תשובה ראשונה: {len(members or [])} רשומות עבור {team_code}/{season_code})")
            printed_debug_sample = True

        for member in members or []:
            person = (member or {}).get("person") or {}
            player_code = person.get("code")
            full_name = person.get("name")
            if not player_code or not full_name:
                continue
            country = person.get("country") or {}
            db.upsert_player(conn, player_code, full_name, country.get("code"), country.get("name"))
            added += 1

        if i % 20 == 0:
            conn.commit()
            print(f"  התקדמות: {i}/{len(team_seasons)} (נוספו/עודכנו {added})")

        time.sleep(REQUEST_DELAY_SECONDS)

    conn.commit()
    conn.close()

    print(f"\nסיום. נוספו/עודכנו {added} שורות שחקן מתוך סגלים רשמיים.")
    if failure_reasons:
        print("כישלונות:")
        for reason, count in failure_reasons.most_common():
            print(f"  {count:4d}x  {reason}")


if __name__ == "__main__":
    main()
