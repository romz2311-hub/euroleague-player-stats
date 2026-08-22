"""מציג טבלה קריאה של הנתונים שנאספו - להרצה מהירה כדי לראות שהכל עובד."""
import pandas as pd

import db


def main():
    conn = db.get_connection()

    print("=== 15 המובילים בנקודות (כל הזמנים, קטגוריית traditional) ===")
    top_scorers = pd.read_sql_query(
        """
        SELECT p.full_name, s.team_code, s.season_code, s.stat_value AS points
        FROM player_stats s
        JOIN players p ON p.player_code = s.player_code
        WHERE s.category = 'traditional' AND s.stat_name = 'pointsScored'
        ORDER BY s.stat_value DESC
        LIMIT 15
        """,
        conn,
    )
    print(top_scorers.to_string(index=False))

    print("\n=== מספר עונות-שחקן לכל קבוצה (כל הזמנים) ===")
    per_team = pd.read_sql_query(
        """
        SELECT t.team_name, COUNT(DISTINCT s.player_code || s.season_code) AS player_seasons
        FROM player_stats s
        JOIN teams t ON t.team_code = s.team_code
        WHERE s.category = 'traditional'
        GROUP BY t.team_name
        ORDER BY player_seasons DESC
        """,
        conn,
    )
    print(per_team.to_string(index=False))

    print("\n=== קטגוריות שנשמרו ועונות שנמצאו ===")
    seasons = pd.read_sql_query(
        """
        SELECT category, MIN(season_code) AS first_season, MAX(season_code) AS last_season, COUNT(DISTINCT season_code) AS n_seasons
        FROM player_stats
        GROUP BY category
        """,
        conn,
    )
    print(seasons.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
