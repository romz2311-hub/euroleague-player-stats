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

**מומלץ לפני ריצה מלאה** - להריץ קודם בדיקה מהירה שרק מציגה את שמות העמודות
שחוזרות מכל קטגוריה, בלי לגעת ב-DB (ראה אזהרה למטה למה זה חשוב):

```bash
python main.py --debug-columns
```

אחרי שזה עובד בלי שגיאות, ריצה מלאה (שולפת **את כל** העונות שה-API מכיר,
בכל 4 הקטגוריות - זה יכול לקחת כמה דקות):

```bash
python main.py
```

זה שומר הכל ב-`data/euroleague.db`.

## ⚠️ שני דברים חשובים לדעת

**1. טווח העונות** - "כל ההיסטוריה" זה כל מה שה-API הרשמי של היורוליג עצמו
מחזיק, לא בהכרח מאז 1958 (תחילת הגביע האירופי הישן). ייתכן שהמידע מתחיל
רק מסביב לעונת 2000-01, כשהמותג "יורוליג" הוקם. `show_stats.py` מראה לך
את טווח העונות שבאמת נשלף.

**2. אין נתוני מדינה/אזרחות** - ה-API לא חושף שדה מדינה של שחקן בשום
נקודת קצה שבדקנו. לכן `country_code`/`country_name` בטבלת `players` תמיד
ריקים כרגע, ו-`query_stats(..., country_name=...)` תמיד תחזיר רשימה ריקה.
פיצול לפי **קבוצה** עובד ומאומת. פיצול לפי **מדינה** ידרוש מקור נתונים נוסף
(למשל דפי הפרופיל של שחקנים באתר הרשמי) - עוד לא מומש.

**אם הריצה נכשלת** עם שגיאה על "עמודות חסרות" (יכול לקרות בקטגוריות
advanced/misc/scoring שלא נבדקו בפועל עדיין - רק traditional נבדק מול
שרת אמיתי) - תריץ `python main.py --debug-columns`, תעתיק את הפלט
ותשלח לי ואני אתקן את `IDENTITY_CANDIDATES` ב-`scraper.py`.

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
