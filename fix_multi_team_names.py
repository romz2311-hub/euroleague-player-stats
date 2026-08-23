"""ניקוי חד-פעמי: שחקן שעבר קבוצה באמצע עונה נשמר לפעמים עם שתי קבוצות
מחוברות במחרוזת אחת ("קבוצה א;קבוצה ב") - זה תוקן ב-scraper.py כדי שלא
יקרה יותר בהרצות חדשות, אבל נתונים שכבר נאספו לפני התיקון צריכים ניקוי.

לוקח את הקבוצה הראשונה בלבד מכל צירוף כזה (אי אפשר לדעת מהנתונים הקיימים
כמה מהסטטיסטיקה שייכת לכל קבוצה בנפרד).

שימוש:
    python fix_multi_team_names.py
"""
import db


def main():
    conn = db.get_connection()
    bad_teams = conn.execute(
        "SELECT team_code, team_name FROM teams WHERE team_code LIKE '%;%' OR team_name LIKE '%;%'"
    ).fetchall()

    print(f"נמצאו {len(bad_teams)} רשומות קבוצה עם כמה קבוצות מחוברות.")

    for team_code, team_name in bad_teams:
        first_code = team_code.split(";")[0].strip()
        first_name = team_name.split(";")[0].strip()

        db.upsert_team(conn, first_code, first_name)
        conn.execute(
            "UPDATE player_stats SET team_code = ? WHERE team_code = ?",
            (first_code, team_code),
        )
        conn.execute("DELETE FROM teams WHERE team_code = ?", (team_code,))
        print(f"  '{team_name}' -> '{first_name}'")

    conn.commit()
    conn.close()
    print("סיום ניקוי.")


if __name__ == "__main__":
    main()
