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

## ⚠️ מגבלה ידועה: אין נתוני מדינה/אזרחות

ה-API של היורוליג לא חושף שדה מדינה בנקודת הקצה של סטטיסטיקת שחקנים
(traditional player stats) - בדקנו את זה מול הריצה האמיתית. לכן `country_code`
ו-`country_name` בטבלת `players` תמיד יהיו ריקים כרגע, ו-`stats_by_country`
תמיד תחזיר רשימה ריקה.

פיצול לפי **קבוצה** עובד ומאומת. פיצול לפי **מדינה** ידרוש מקור נתונים נוסף
(למשל סקרייפינג של דפי הפרופיל של השחקנים באתר הרשמי) - זה עוד לא מומש.

אם `python main.py --season <שנה>` נכשל עם שגיאה על "עמודות חסרות" (למשל
אחרי שינוי ב-API בעתיד), תריץ:

```bash
python main.py --season 2024 --debug-columns
```

זה ידפיס את שמות העמודות האמיתיים בלי לגעת ב-DB. תעדכן/י לפי זה את
`CANDIDATES` ב-`scraper.py`, או תשלח/י לי את הפלט ואני אתקן.

## שאילתות לדוגמה

```python
import db

conn = db.get_connection()

# כל השחקנים של מכבי תל אביב (קוד הקבוצה משתנה לפי עונה, אפשר לבדוק בטבלת teams)
rows = db.stats_by_team(conn, "TEL")
```

או ישירות מה-shell:

```bash
sqlite3 data/euroleague.db "SELECT full_name, points FROM player_season_stats JOIN players USING(player_code) WHERE team_code = 'TEL';"
```

## מקור הנתונים

החבילה [`euroleague-api`](https://github.com/giasemidis/euroleague_api) -
עוטפת את ה-API הרשמי של היורוליג (`api-live.euroleague.net`).
