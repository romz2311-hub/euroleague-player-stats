"""בדיקה חד-פעמית: שולף פרופיל של שחקן בודד מה-API, כדי לראות את המבנה
האמיתי של נתוני המדינה - לפני שבונים תהליך מלא שמושך את זה לכל השחקנים.

שימוש:
    python test_person_bio.py <player_code>

את player_code אפשר לקחת מטבלת players ב-DB, למשל:
    python -c "import db; c = db.get_connection(); print(c.execute('SELECT player_code, full_name FROM players LIMIT 5').fetchall())"
"""
import json
import sys

import requests

BASE_URL = "https://api-live.euroleague.net"


def main():
    if len(sys.argv) < 2:
        print("שימוש: python test_person_bio.py <player_code>")
        return

    player_code = sys.argv[1]
    url = f"{BASE_URL}/v2/people/{player_code}"
    response = requests.get(url, timeout=15)
    print(f"URL: {url}")
    print(f"סטטוס: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:5000])
    except ValueError:
        print("(לא JSON) גוף התשובה:")
        print(response.text[:2000])


if __name__ == "__main__":
    main()
