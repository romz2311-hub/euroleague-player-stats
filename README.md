# Euroleague Player Stats

סקרייפר וסטטיסטיקות שחקני יורוליג לכל ההיסטוריה, שמורות במסד נתונים מקומי
(SQLite), עם אפשרות לשלוף לפי קבוצה, לפי מדינה, ולפי קטגוריית סטטיסטיקה
(traditional / advanced / misc / scoring), מסודר כרונולוגית.

## התקנה

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## שימוש

ריצה מלאה - שולפת **עונה-עונה** (מ-2000, הקמת היורוליג בפורמט הנוכחי, ועד
היום), בכל 4 הקטגוריות. זה הרבה קריאות API אז זה יכול לקחת כמה דקות:

```bash
python main.py
```

זה שומר הכל ב-`data/euroleague.db`. עונה שנכשלת (למשל לא קיימת ב-API) פשוט
מדולגת, עם הודעה בטרמינל - לא מפילה את כל הריצה.

לבדיקה מהירה יותר על טווח עונות קטן:

```bash
python main.py --start-season 2022
```

## ⚠️ שני דברים חשובים לדעת

**1. אין נתוני מדינה/אזרחות** - ה-API לא חושף שדה מדינה של שחקן בשום
נקודת קצה שבדקנו. לכן `country_code`/`country_name` בטבלת `players` תמיד
ריקים כרגע, ו-`query_stats(..., country_name=...)` תמיד תחזיר רשימה ריקה.
פיצול לפי **קבוצה** עובד ומאומת. פיצול לפי **מדינה** ידרוש מקור נתונים נוסף
(למשל דפי הפרופיל של שחקנים באתר הרשמי) - עוד לא מומש.

**2. קטגוריית `scoring` לא נבדקה בפועל** - traditional/advanced/misc כן
נבדקו מול שרת אמיתי ועובדות. אם הריצה נכשלת עם שגיאה על "עמודות חסרות"
(בעיקר סיכוי שזה יקרה ב-scoring), תריץ:

```bash
python main.py --debug-columns --category scoring --season 2024
```

תעתיק את הפלט ותשלח לי ואני אתקן את `IDENTITY_CANDIDATES` ב-`scraper.py`.

## שאילתות לדוגמה

```python
import db

conn = db.get_connection()

# כל הסטטיסטיקה של כל השחקנים של מכבי תל אביב, כרונולוגית
rows = db.query_stats(conn, team_code="TEL")

# רק סטטיסטיקה מתקדמת (advanced)
rows = db.query_stats(conn, category="advanced")
```

לראות תמונה מהירה של הנתונים:

```bash
python show_stats.py
```

## מקור הנתונים

החבילה [`euroleague-api`](https://github.com/giasemidis/euroleague_api) -
עוטפת את ה-API הרשמי של היורוליג (`api-live.euroleague.net`).
