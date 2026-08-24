"""מציג את כל שורות ה-box-score הגולמיות של שחקן (לפי חלק משם), כדי לבדוק
אם ממוצע שנראה לא הגיוני נובע ממדגם קטן מדי או מבאג אמיתי בנתונים.

שימוש:
    python debug_player_games.py HANKINS
"""
import sys

import db


def main():
    if len(sys.argv) < 2:
        print("שימוש: python debug_player_games.py <חלק משם>")
        return

    query_text = sys.argv[1].upper()
    conn = db.get_connection()

    rows = conn.execute(
        """
        SELECT p.full_name, g.season_code, g.game_code, g.round_number, g.team_code,
               g.is_starter, g.is_playing, g.minutes, g.points, g.total_rebounds, g.assists, g.valuation
        FROM player_game_stats g
        JOIN players p ON p.player_code = g.player_code
        WHERE p.full_name LIKE ?
        ORDER BY p.full_name, g.season_code, g.game_code
        """,
        (f"%{query_text}%",),
    ).fetchall()

    if not rows:
        print(f"לא נמצאו שורות box-score עבור '{query_text}'.")
        return

    print(f"נמצאו {len(rows)} שורות (משחקים) עבור '{query_text}':\n")
    for row in rows:
        (full_name, season_code, game_code, round_number, team_code,
         is_starter, is_playing, minutes, points, total_rebounds, assists, valuation) = row
        print(f"{full_name} | {season_code} | game {game_code} (round {round_number}) | {team_code} | "
              f"starter={is_starter} playing={is_playing} min={minutes} | "
              f"pts={points} reb={total_rebounds} ast={assists} pir={valuation}")

    conn.close()


if __name__ == "__main__":
    main()
