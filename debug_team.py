"""בדיקה חד-פעמית: כמה שחקנים משויכים לקבוצה מסוימת (לפי חלק משם), ובאילו עונות.

שימוש:
    python debug_team.py הפועל
    python debug_team.py Hapoel
"""
import sys

import db


def main():
    if len(sys.argv) < 2:
        print("שימוש: python debug_team.py <חלק משם הקבוצה>")
        return

    query_text = sys.argv[1]
    conn = db.get_connection()

    teams = conn.execute(
        "SELECT team_code, team_name FROM teams WHERE team_name LIKE ?",
        (f"%{query_text}%",),
    ).fetchall()
    print(f"קבוצות תואמות בטבלת teams: {teams}")

    for team_code, team_name in teams:
        rows = conn.execute(
            """
            SELECT season_code, COUNT(DISTINCT player_code) AS players
            FROM player_stats
            WHERE team_code = ?
            GROUP BY season_code
            ORDER BY season_code
            """,
            (team_code,),
        ).fetchall()
        print(f"\n{team_name} ({team_code}) - שחקנים לפי עונה:")
        for season_code, players in rows:
            print(f"  {season_code}: {players} שחקנים")

    conn.close()


if __name__ == "__main__":
    main()
