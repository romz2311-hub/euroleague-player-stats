"""מציג טבלה קריאה של הנתונים שנאספו - להרצה מהירה כדי לראות שהכל עובד."""
import pandas as pd

import db


def main():
    conn = db.get_connection()

    print("=== 15 המובילים בנקודות לעונה ===")
    top_scorers = pd.read_sql_query(
        """
        SELECT p.full_name, s.team_code, s.games_played, s.points, s.total_rebounds, s.assists, s.pir
        FROM player_season_stats s
        JOIN players p ON p.player_code = s.player_code
        ORDER BY s.points DESC
        LIMIT 15
        """,
        conn,
    )
    print(top_scorers.to_string(index=False))

    print("\n=== מספר שחקנים לכל קבוצה ===")
    per_team = pd.read_sql_query(
        """
        SELECT t.team_name, COUNT(*) AS players
        FROM player_season_stats s
        JOIN teams t ON t.team_code = s.team_code
        GROUP BY t.team_name
        ORDER BY players DESC
        """,
        conn,
    )
    print(per_team.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
