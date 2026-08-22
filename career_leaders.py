"""ממוצעי קריירה לכל שחקן על פני כל ההיסטוריה שנשמרה ב-DB (2000 ואילך),
משוקלל לפי מספר משחקים בכל עונה. דורש שכבר הרצת `python main.py` וגם
`python fetch_countries.py` (אם רוצים לסנן לפי מדינה).

שימוש:
    python career_leaders.py
    python career_leaders.py --stat assists --min-games 50
    python career_leaders.py --country Israel
"""
import argparse

import pandas as pd

import db

# שמות סטטיסטיקה נפוצים בקטגוריית traditional (ראה show_stats.py / --debug-columns לרשימה מלאה)
COMMON_STATS = [
    "pointsScored", "totalRebounds", "assists", "steals", "turnovers",
    "blocks", "pir", "minutesPlayed",
]


def main():
    parser = argparse.ArgumentParser(description="Euroleague career averages leaderboard")
    parser.add_argument("--category", default="traditional", choices=["traditional", "advanced", "misc", "scoring"])
    parser.add_argument("--stat", default="pointsScored", help=f"שם הסטטיסטיקה, למשל: {', '.join(COMMON_STATS)}")
    parser.add_argument("--min-games", type=int, default=100, help="מינימום משחקי קריירה כדי להיכלל בדירוג")
    parser.add_argument("--country", default=None, help="לסנן רק לשחקנים ממדינה מסוימת, למשל Israel")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    conn = db.get_connection()
    rows = db.career_averages(conn, args.category, args.stat, args.min_games, args.country)
    conn.close()

    if not rows:
        print(f"לא נמצאו נתונים עבור {args.category}/{args.stat}"
              + (f" במדינה {args.country}" if args.country else "")
              + ". ודא שהרצת python main.py (וגם python fetch_countries.py אם סיננת לפי מדינה).")
        return

    df = pd.DataFrame(rows, columns=["player", "country", f"career_avg_{args.stat}", "total_games", "seasons"])
    title = f"=== מובילי קריירה ב-{args.stat} (מינימום {args.min_games} משחקים, מ-2000 ואילך)"
    if args.country:
        title += f", מדינה: {args.country}"
    title += " ==="
    print(title)
    print(df.head(args.top).to_string(index=False))


if __name__ == "__main__":
    main()
