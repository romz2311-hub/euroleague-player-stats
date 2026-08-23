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

**אחרי** ש-`python main.py` סיים, מריצים פעם אחת (איטי - קריאת רשת נפרדת
לכל שחקן) כדי להשלים מדינת אזרחות לכל שחקן:

```bash
python fetch_countries.py
```

## ⚠️ דבר חשוב לדעת

קטגוריית `scoring` לא נבדקה בפועל בזמן שהקוד נכתב - traditional/advanced/misc
כן נבדקו מול שרת אמיתי ועובדות. אם הריצה נכשלת עם שגיאה על "עמודות חסרות"
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

# כל הסטטיסטיקה של שחקנים ישראלים (אחרי הרצת fetch_countries.py)
rows = db.query_stats(conn, country_name="Israel")
```

ממוצעי קריירה (משוקללים לפי מספר משחקים), אפשר גם לפי מדינה:

```bash
python career_leaders.py --country Israel
```

לראות תמונה מהירה של הנתונים בטרמינל:

```bash
python show_stats.py
```

## דשבורד ויזואלי

כדי לבנות דף HTML יחיד עם דשבורד ויזואלי (כרטיסי סיכום, גרפים, וטבלה
מלאה עם חיפוש ומיון), כולל פאנל סינון אינטראקטיבי לפי קבוצה / מדינה /
עונה (או "כל הזמנים") / סוג סטטיסטיקה (נקודות, ריבאונדים, אסיסטים ועוד) -
דורש שכבר הרצת `python main.py` ו-`python fetch_countries.py`:

```bash
python build_dashboard.py
```

זה יוצר קובץ `dashboard.html` בתיקיית הפרויקט - פשוט תלחץ עליו לחיצה
כפולה כדי לפתוח בדפדפן. הכל רץ בתוך הדפדפן בלי צורך באינטרנט או בשרת -
כל הנתונים כבר מוטמעים בקובץ.

## עדכון אוטומטי

`update_all.py` מריץ ברצף: רענון סטטיסטיקה לעונה הנוכחית בלבד (לא כל
ההיסטוריה - זה מהיר), סגלים רשמיים, מדינות לשחקנים חדשים, ובניית
הדשבורד מחדש:

```bash
python update_all.py
```

כדי שזה ירוץ **לבד**, בלי שתצטרך להריץ פקודות ידנית, אפשר לתזמן את זה
ב-Windows עם Task Scheduler (מובנה בווינדוס, לא צריך להתקין כלום):

1. פתח את תפריט התחל, חפש "Task Scheduler" ופתח אותו
2. בצד ימין, לחץ "Create Basic Task..."
3. תן שם, למשל "Euroleague Stats Update", Next
4. תבחר תדירות (למשל Daily), Next, תבחר שעה, Next
5. Action: "Start a program", Next
6. ב-"Program/script" תלחץ Browse ותבחר את הקובץ `run_update.bat`
   בתיקיית הפרויקט (`run_update.bat` - כבר מכין את הסביבה הוירטואלית
   ומריץ הכל)
7. Next, Finish

מכאן זה ירוץ אוטומטית בכל יום (או מה שבחרת), והפלט/שגיאות יישמרו
בקובץ `update_log.txt` בתיקיית הפרויקט - כדאי להציץ בו מדי פעם לוודא
שאין כישלונות.

## מקור הנתונים

החבילה [`euroleague-api`](https://github.com/giasemidis/euroleague_api) -
עוטפת את ה-API הרשמי של היורוליג (`api-live.euroleague.net`).
