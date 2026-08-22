"""ממוצעי קריירה לכל שחקן על פני כל ההיסטוריה שנשמרה ב-DB (2000 ואילך),
משוקלל לפי מספר משחקים בכל עונה. דורש שכבר הרצת `python main.py` לפחות פעם אחת.

שימוש:
    python career_leaders.py
    python career_leaders.py --stat assists --min-games 50
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
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    conn = db.get_connection()
    rows = db.career_averages(conn, args.category, args.stat, args.min_games)
    conn.close()

    if not rows:
        print(f"לא נמצאו נתונים עבור {args.category}/{args.stat}. ודא שהרצת קודם python main.py.")
        return

    df = pd.DataFrame(rows, columns=["player", f"career_avg_{args.stat}", "total_games", "seasons"])
    print(f"=== מובילי קריירה ב-{args.stat} (מינימום {args.min_games} משחקים, מ-2000 ואילך) ===")
    print(df.head(args.top).to_string(index=False))


if __name__ == "__main__":
    main()
