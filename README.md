# Euroleague Player Stats

סקרייפר וסטטיסטיקות שחקני יורוליג, שמורות במסד נתונים מקומי (SQLite),
עם אפשרות לשלוף נתונים לפי מדינת שחקן או לפי קבוצה.

## התקנה

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## שימוש

```bash
python main.py --season 2024
```

זה שולף את כל סטטיסטיקת השחקנים של עונת 2024-25 ושומר אותה ב-`data/euroleague.db`.

## ⚠️ הערה חשובה לפני ריצה ראשונה

הקוד נכתב בסביבה שחסמה גישה חיצונית ל-API של היורוליג, ולכן שמות העמודות
המדויקות שחוזרות מה-API (ב-`scraper.py`, המשתנה `CANDIDATES`) לא אומתו מול
שרת אמיתי. אם ריצה ראשונה נכשלת עם שגיאה על "עמודות חסרות", תריץ:

```bash
python main.py --season 2024 --debug-columns
```

זה ידפיס את שמות העמודות האמיתיים בלי לגעת ב-DB. תעדכן/י לפי זה את
`CANDIDATES` ב-`scraper.py`, או תשלח/י לי את הפלט ואני אתקן.

## שאילתות לדוגמה

```python
import db

conn = db.get_connection()

# כל השחקנים מישראל
rows = db.stats_by_country(conn, "Israel")

# כל השחקנים של מכבי תל אביב (קוד הקבוצה משתנה לפי עונה, אפשר לבדוק בטבלת teams)
rows = db.stats_by_team(conn, "TEL")
```

או ישירות מה-shell:

```bash
sqlite3 data/euroleague.db "SELECT full_name, country_name, points FROM player_season_stats JOIN players USING(player_code) WHERE country_name = 'Israel';"
```

## מקור הנתונים

החבילה [`euroleague-api`](https://github.com/giasemidis/euroleague_api) -
עוטפת את ה-API הרשמי של היורוליג (`api-live.euroleague.net`).
