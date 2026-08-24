"""ניקוי חד-פעמי: מוחק שורות "Total"/"Team" שנכנסו ל-DB בטעות כאילו היו
שחקנים (אלה שורות סיכום קבוצתי מה-API של ה-box-score). זה תוקן ב-
fetch_boxscores.py כדי שלא יקרה יותר בהרצות חדשות.

שימוש:
    python fix_total_rows.py
"""
import db


def main():
    conn = db.get_connection()

    bad_players = conn.execute(
        "SELECT player_code, full_name FROM players WHERE UPPER(TRIM(full_name)) IN ('TOTAL', 'TEAM')"
    ).fetchall()

    print(f"נמצאו {len(bad_players)} רשומות 'שחקן' שהן בעצם סיכומי קבוצה.")

    for player_code, full_name in bad_players:
        deleted = conn.execute(
            "DELETE FROM player_game_stats WHERE player_code = ?", (player_code,)
        ).rowcount
        conn.execute("DELETE FROM players WHERE player_code = ?", (player_code,))
        print(f"  '{full_name}' ({player_code}): נמחקו {deleted} שורות box-score")

    conn.commit()
    conn.close()
    print("סיום ניקוי.")


if __name__ == "__main__":
    main()
