"""רשימת שחקנים גולמית - כל שחקן שקיים ב-DB, בלי שום סינון לפי מספר משחקים.
אפשר לסנן לפי מדינה ו/או קבוצה.

שימוש:
    python list_players.py --country Israel
    python list_players.py --team TEL
"""
import argparse

import db


def main():
    parser = argparse.ArgumentParser(description="רשימת שחקנים גולמית מה-DB")
    parser.add_argument("--country", default=None, help="למשל Israel")
    parser.add_argument("--team", default=None, help="קוד קבוצה, למשל TEL")
    args = parser.parse_args()

    conn = db.get_connection()
    query = "SELECT player_code, full_name, country_name FROM players WHERE 1=1"
    params = []
    if args.country:
        query += " AND country_name = ?"
        params.append(args.country)
    if args.team:
        query += " AND player_code IN (SELECT DISTINCT player_code FROM player_stats WHERE team_code = ?)"
        params.append(args.team)
    query += " ORDER BY full_name"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    print(f"נמצאו {len(rows)} שחקנים")
    for player_code, full_name, country_name in rows:
        print(f"{player_code}  {full_name}  {country_name or '(אין מדינה)'}")


if __name__ == "__main__":
    main()
