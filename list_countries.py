"""מציג כמה שחקנים (עם מדינה ידועה) יש לכל מדינה ב-DB, מהגבוה לנמוך.
דורש שכבר הרצת python fetch_countries.py.

שימוש:
    python list_countries.py
"""
import db


def main():
    conn = db.get_connection()
    rows = db.countries_summary(conn)
    conn.close()

    if not rows:
        print("אין עדיין נתוני מדינה. תריץ קודם python fetch_countries.py")
        return

    for country_name, players in rows:
        print(f"{players:4d}  {country_name}")


if __name__ == "__main__":
    main()
