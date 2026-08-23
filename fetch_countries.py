"""משלים מדינת אזרחות לכל שחקן שכבר קיים בטבלת players, דרך נקודת הקצה
האישית של כל שחקן (v2/people/{קוד}) - שם, ורק שם, יש נתון מדינה.

זו קריאת רשת נפרדת לכל שחקן (יש כמה מאות/אלפים שחקנים ב-DB אחרי
python main.py), אז זה איטי ולוקח כמה דקות. יש השהיה קטנה בין קריאות
כדי לא להעמיס על השרת.

שימוש:
    python fetch_countries.py
"""
import time
from collections import Counter

import requests

import db

BASE_URL = "https://api-live.euroleague.net"
REQUEST_DELAY_SECONDS = 0.3


def fetch_country(player_code: str):
    """מחזיר (country_code, country_name, reason_if_failed).
    reason הוא None אם הצליח, אחרת מחרוזת שמסבירה את הכישלון (סטטוס HTTP וכו')."""
    url = f"{BASE_URL}/v2/people/{player_code}"
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        return None, None, f"HTTP {response.status_code}"

    body = response.json()
    country = body.get("country") or {}
    if not country.get("name"):
        return None, None, "200 אבל בלי שדה country בתשובה"

    return country.get("code"), country.get("name"), None


def main():
    conn = db.get_connection()
    players = conn.execute(
        "SELECT player_code FROM players WHERE country_name IS NULL"
    ).fetchall()

    print(f"נמצאו {len(players)} שחקנים בלי מדינה. שולף אחד-אחד...")

    updated = 0
    failure_reasons = Counter()
    failure_examples = {}

    for i, (player_code,) in enumerate(players, start=1):
        try:
            country_code, country_name, reason = fetch_country(player_code)
        except Exception as exc:
            reason = f"exception: {exc}"
            country_code = country_name = None

        if reason is None:
            conn.execute(
                "UPDATE players SET country_code = ?, country_name = ? WHERE player_code = ?",
                (country_code, country_name, player_code),
            )
            updated += 1
        else:
            failure_reasons[reason] += 1
            failure_examples.setdefault(reason, []).append(player_code)

        if i % 50 == 0:
            conn.commit()
            print(f"  התקדמות: {i}/{len(players)} (עודכנו {updated}, נכשלו {sum(failure_reasons.values())})")

        time.sleep(REQUEST_DELAY_SECONDS)

    conn.commit()
    conn.close()

    total_failed = sum(failure_reasons.values())
    print(f"\nסיום. עודכנו {updated} שחקנים עם מדינה, {total_failed} נכשלו.")
    if failure_reasons:
        print("\nפירוט סיבות הכישלון:")
        for reason, count in failure_reasons.most_common():
            examples = ", ".join(failure_examples[reason][:5])
            print(f"  {count:4d}x  {reason}  (דוגמאות קוד שחקן: {examples})")


if __name__ == "__main__":
    main()
