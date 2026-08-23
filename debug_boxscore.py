"""בדיקה חד-פעמית: מציג את שמות העמודות שחוזרות מנתוני ה-boxscore (סטטיסטיקה
לפי משחק בודד, לא לפי עונה) - זה מקור נתונים אחר לגמרי מזה שכבר משתמשים בו,
אז לא בטוחים בשמות העמודות. לא שומר כלום ב-DB.

שימוש:
    python debug_boxscore.py 2025
"""
import sys

from euroleague_api.boxscore_data import BoxScoreData


def main():
    if len(sys.argv) < 2:
        print("שימוש: python debug_boxscore.py <עונה>")
        return

    season = int(sys.argv[1])
    boxscore = BoxScoreData("E")
    df = boxscore.get_players_boxscore_stats_single_season(season)

    print(f"סה\"כ שורות: {len(df)}")
    print(f"\nעמודות:\n{list(df.columns)}")
    print(f"\n3 שורות ראשונות:\n{df.head(3).to_string()}")

    # נחפש אם GINAT נמצא כאן, כדי לבדוק אם זה מקור טוב יותר
    name_cols = [c for c in df.columns if "name" in c.lower() or c.lower() == "player"]
    for col in name_cols:
        matches = df[df[col].astype(str).str.upper().str.contains("GINAT", na=False)]
        if not matches.empty:
            print(f"\nנמצא GINAT בעמודה '{col}':")
            print(matches.to_string())


if __name__ == "__main__":
    main()
