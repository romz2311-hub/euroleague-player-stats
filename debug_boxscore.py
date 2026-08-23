"""בדיקה חד-פעמית: מציג את שמות העמודות שחוזרות מנתוני ה-boxscore (סטטיסטיקה
לפי משחק בודד) - מקור נתונים שונה מזה שכבר משתמשים בו, לא בטוחים בשמות
העמודות. כותב את התוצאה לקובץ טקסט נקי (בלי הרעש של פס ההתקדמות של השליפה),
ושומר קאש ל-CSV כדי שלא נצטרך לשלוף שוב מה-API בכל בדיקה (זה לוקח דקות
ופוגע בהגבלות קצב).

שימוש:
    python debug_boxscore.py 2025
    python debug_boxscore.py 2025 GINAT   # לחפש שם ספציפי בנוסף
"""
import sys
from pathlib import Path

import pandas as pd

from euroleague_api.boxscore_data import BoxScoreData


def main():
    if len(sys.argv) < 2:
        print("שימוש: python debug_boxscore.py <עונה> [שם לחיפוש]")
        return

    season = int(sys.argv[1])
    search_name = sys.argv[2].upper() if len(sys.argv) > 2 else None

    cache_path = Path(f"data/boxscore_{season}_raw.csv")

    if cache_path.exists():
        print(f"טוען מקאש קיים: {cache_path} (למחוק את הקובץ אם רוצים לשלוף מחדש מה-API)")
        df = pd.read_csv(cache_path)
    else:
        print("שולף מה-API - זה יכול לקחת כמה דקות...")
        boxscore = BoxScoreData("E")
        df = boxscore.get_players_boxscore_stats_single_season(season)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        print(f"נשמר קאש ל-{cache_path}")

    output_path = Path("boxscore_debug_output.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f'סה"כ שורות: {len(df)}\n\n')
        f.write(f"עמודות:\n{list(df.columns)}\n\n")
        f.write(f"3 שורות ראשונות:\n{df.head(3).to_string()}\n\n")

        if search_name:
            name_cols = [c for c in df.columns if "name" in c.lower() or c.lower() == "player"]
            for col in name_cols:
                matches = df[df[col].astype(str).str.upper().str.contains(search_name, na=False)]
                f.write(f"\n--- חיפוש '{search_name}' בעמודה '{col}': {len(matches)} התאמות ---\n")
                if not matches.empty:
                    f.write(matches.to_string() + "\n")

    print(f"\nהפלט המלא נשמר ב-{output_path} (בתיקיית הפרויקט) - תפתח אותו ותשלח לי את התוכן.")


if __name__ == "__main__":
    main()
