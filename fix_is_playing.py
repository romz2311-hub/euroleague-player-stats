"""תיקון חד-פעמי: עדכון עמודת is_playing לכל השורות שכבר נשמרו ב-DB,
לפי שדה הדקות (minutes) במקום ה-IsPlaying הלא אמין שקיבלנו מה-API.
לא צריך לשלוף שוב מה-API - זה עדכון מקומי בלבד, מהיר.

שימוש:
    python fix_is_playing.py
"""
import db


def main():
    conn = db.get_connection()

    rows = conn.execute("SELECT player_code, season_code, game_code, minutes, is_playing FROM player_game_stats").fetchall()
    updated = 0

    for player_code, season_code, game_code, minutes, old_is_playing in rows:
        correct_is_playing = 1 if minutes and str(minutes).strip().upper() != "DNP" else 0
        if correct_is_playing != old_is_playing:
            conn.execute(
                "UPDATE player_game_stats SET is_playing = ? WHERE player_code = ? AND season_code = ? AND game_code = ?",
                (correct_is_playing, player_code, season_code, game_code),
            )
            updated += 1

    conn.commit()
    conn.close()
    print(f"נבדקו {len(rows)} שורות, תוקנו {updated}.")


if __name__ == "__main__":
    main()
