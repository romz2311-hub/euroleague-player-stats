"""בדיקה חד-פעמית: מחפש שחקן ישירות בתשובה הגולמית של ה-API (קטגוריית
traditional, עונה נתונה) - בלי לעבור דרך ה-DB שלנו בכלל. עוזר לדעת אם
שחקן חסר כי ה-API עצמו לא מחזיר אותו, או כי הוא אבד איפשהו אצלנו בדרך.

שימוש:
    python debug_player_search.py 2025 GINAT
"""
import sys

import scraper


def main():
    if len(sys.argv) < 3:
        print("שימוש: python debug_player_search.py <עונה> <חלק משם>")
        return

    season = int(sys.argv[1])
    query_text = sys.argv[2].upper()

    df = scraper.fetch_category_single_season("traditional", season)
    print(f"סה\"כ שורות שחזרו מה-API עבור עונת {season} (traditional): {len(df)}")

    name_col = "player.name" if "player.name" in df.columns else None
    if not name_col:
        print(f"לא נמצאה עמודת שם שחקן. עמודות קיימות: {list(df.columns)}")
        return

    matches = df[df[name_col].astype(str).str.upper().str.contains(query_text, na=False)]
    if matches.empty:
        print(f"'{query_text}' לא נמצא בכלל בתשובת ה-API הגולמית לעונה {season}.")
    else:
        print(f"נמצאו {len(matches)} התאמות:")
        cols_to_show = [c for c in ["player.code", "player.name", "player.team.code", "player.team.name", "gamesPlayed", "pointsScored"] if c in df.columns]
        print(matches[cols_to_show].to_string(index=False))


if __name__ == "__main__":
    main()
