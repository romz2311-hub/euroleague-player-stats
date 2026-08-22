"""משלים מדינת אזרחות לכל שחקן שכבר קיים בטבלת players, דרך נקודת הקצה
האישית של כל שחקן (v2/people/{קוד}) - שם, ורק שם, יש נתון מדינה.

זו קריאת רשת נפרדת לכל שחקן (יש כמה מאות/אלפים שחקנים ב-DB אחרי
python main.py), אז זה איטי ולוקח כמה דקות. יש השהיה קטנה בין קריאות
כדי לא להעמיס על השרת.

שימוש:
    python fetch_countries.py
"""
import time

import requests

import db

BASE_URL = "https://api-live.euroleague.net"
REQUEST_DELAY_SECONDS = 0.3


def fetch_country(player_code: str):
    """מחזיר (country_code, country_name) לשחקן, או (None, None) אם לא נמצא."""
    url = f"{BASE_URL}/v2/people/{player_code}"
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        return None, None
    country = response.json().get("country") or {}
    return country.get("code"), country.get("name")


def main():
    conn = db.get_connection()
    players = conn.execute(
        "SELECT player_code FROM players WHERE country_name IS NULL"
    ).fetchall()

    print(f"נמצאו {len(players)} שחקנים בלי מדינה. שולף אחד-אחד...")

    updated = 0
    failed = 0
    for i, (player_code,) in enumerate(players, start=1):
        try:
            country_code, country_name = fetch_country(player_code)
        except Exception as exc:
            print(f"  {player_code}: שגיאה ({exc})")
            failed += 1
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        if country_name:
            conn.execute(
                "UPDATE players SET country_code = ?, country_name = ? WHERE player_code = ?",
                (country_code, country_name, player_code),
            )
            updated += 1
        else:
            failed += 1

        if i % 50 == 0:
            conn.commit()
            print(f"  התקדמות: {i}/{len(players)}")

        time.sleep(REQUEST_DELAY_SECONDS)

    conn.commit()
    conn.close()
    print(f"סיום. עודכנו {updated} שחקנים עם מדינה, {failed} נכשלו/לא נמצאו.")


if __name__ == "__main__":
    main()
