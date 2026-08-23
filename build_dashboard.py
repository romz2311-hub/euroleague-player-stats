"""בונה דשבורד HTML יחיד ועצמאי (קובץ אחד, בלי שרת) מתוך הנתונים ב-DB, עם
פאנל סינון אינטראקטיבי (קבוצה / מדינה / עונה או כל הזמנים / סוג סטטיסטיקה)
שרץ כולו בדפדפן - כל הנתונים מוטמעים בקובץ, אין צורך בחיבור לאינטרנט אחרי
היצירה.

שימוש:
    python build_dashboard.py
"""
import html
import json
from collections import defaultdict
from datetime import date

import db

OUTPUT_PATH = "dashboard.html"
TOP_COUNTRIES_LIMIT = 15

# שם הסטטיסטיקה ב-DB -> תווית בעברית להצגה. gamesPlayed תמיד מוטמע (למשקל
# ולסינון מינימום משחקים) גם אם לא נבחר כסטטיסטיקה בעצמה.
STAT_LABELS = {
    "pointsScored": "נקודות",
    "totalRebounds": "ריבאונדים",
    "assists": "אסיסטים",
    "steals": "חטיפות",
    "turnovers": "איבודי כדור",
    "blocks": "חסימות",
    "minutesPlayed": "דקות משחק",
    "pir": "PIR (דירוג יעילות)",
    "gamesPlayed": "משחקים ששוחקו",
}


def build_player_season_records(long_rows):
    """הופך שורות EAV (player, country, season, team, stat_name, value) לרשימת
    רשומות player-season מפוברטות: {player, country, season, team, stats:{...}}."""
    grouped = defaultdict(dict)
    meta = {}
    for full_name, country_name, season_code, team_name, stat_name, stat_value in long_rows:
        if stat_name not in STAT_LABELS:
            continue
        key = (full_name, season_code, team_name)
        meta[key] = (full_name, country_name, season_code, team_name)
        grouped[key][stat_name] = stat_value

    records = []
    for key, stats in grouped.items():
        full_name, country_name, season_code, team_name = meta[key]
        records.append({
            "player": full_name,
            "country": country_name,
            "season": season_code,
            "team": team_name,
            "stats": stats,
        })
    return records


def bar_rows(items, value_fmt="{:.1f}"):
    """items: רשימת (label, value). מחזיר HTML של שורות בר-צ'רט אופקי סטטי."""
    if not items:
        return "<p class='empty'>אין נתונים.</p>"
    max_value = max(v for _, v in items) or 1
    rows = []
    for label, value in items:
        pct = max(2, round(value / max_value * 100, 1))
        safe_label = html.escape(str(label))
        value_text = value_fmt.format(value)
        rows.append(
            f"""<div class="bar-row">
                <div class="bar-label">{safe_label}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{pct}%" title="{safe_label}: {value_text}"></div></div>
                <div class="bar-value">{value_text}</div>
            </div>"""
        )
    return "\n".join(rows)


def table_rows(rows):
    out = []
    for full_name, country_name, team_names, total_games, seasons, career_avg in rows:
        out.append(
            "<tr>"
            f"<td>{html.escape(full_name or '')}</td>"
            f"<td>{html.escape(country_name or '')}</td>"
            f"<td>{html.escape(team_names or '')}</td>"
            f"<td data-sort='{seasons or 0}'>{seasons or 0}</td>"
            f"<td data-sort='{total_games or 0}'>{int(total_games) if total_games else 0}</td>"
            f"<td data-sort='{career_avg or 0}'>{f'{career_avg:.1f}' if career_avg is not None else ''}</td>"
            "</tr>"
        )
    return "\n".join(out)


def main():
    conn = db.get_connection()
    overview = db.overview_counts(conn)
    top_countries = db.countries_summary(conn)[:TOP_COUNTRIES_LIMIT]
    full_table = db.full_player_table(conn, category="traditional", stat_name="pointsScored")
    long_rows = db.traditional_long_rows(conn)
    conn.close()

    records = build_player_season_records(long_rows)
    records_json = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    stat_labels_json = json.dumps(STAT_LABELS, ensure_ascii=False)

    countries_bars = bar_rows([(name, count) for name, count in top_countries], value_fmt="{:.0f}")
    table_html = table_rows(full_table)

    season_range = f"{overview['first_season']} – {overview['last_season']}" if overview["first_season"] else "-"

    html_doc = f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>Euroleague Player Stats Dashboard</title>
<style>
  :root {{
    --page: #0a0a0a;
    --surface-1: #161616;
    --surface-2: #1f1f1f;
    --text-primary: #ffffff;
    --text-secondary: #b8b6b0;
    --text-muted: #7d7b76;
    --gridline: #2a2a2a;
    --baseline: #383835;
    --accent: #f2701c;
    --accent-dark: #b7500e;
    --border: rgba(255,255,255,0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background:
      radial-gradient(1200px 400px at 50% -100px, rgba(242,112,28,0.12), transparent),
      var(--page);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 0 0 64px;
  }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
  header.hero {{
    border-bottom: 1px solid var(--border);
    padding: 28px 24px 24px;
    margin-bottom: 28px;
  }}
  header.hero .hero-inner {{ max-width: 1100px; margin: 0 auto; display: flex; align-items: center; gap: 16px; }}
  .logo {{ flex-shrink: 0; }}
  h1 {{
    font-size: 26px; margin: 0 0 4px; letter-spacing: 0.3px;
    background: linear-gradient(90deg, #ffffff, #ffd8ba);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }}
  h1 .accent {{ color: var(--accent); -webkit-text-fill-color: var(--accent); }}
  .subtitle {{ color: var(--text-secondary); margin: 0; font-size: 13px; }}
  .tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .tile {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 10px;
    padding: 16px;
    transition: transform 0.15s ease;
  }}
  .tile:hover {{ transform: translateY(-2px); }}
  .tile .value {{ font-size: 30px; font-weight: 800; font-variant-numeric: tabular-nums; }}
  .tile .label {{ color: var(--text-secondary); font-size: 12px; margin-top: 4px; letter-spacing: 0.2px; }}
  section {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 22px;
    direction: ltr;
  }}
  section h2 {{
    direction: rtl; text-align: right;
    font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0 0 16px;
    display: flex; align-items: center; gap: 8px; justify-content: flex-end;
  }}
  section h2::after {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }}
  .filters {{
    direction: rtl;
    display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;
    align-items: flex-end;
  }}
  .filter-field {{ display: flex; flex-direction: column; gap: 4px; min-width: 150px; }}
  .filter-field label {{ font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.4px; }}
  .filter-field select, .filter-field input {{
    padding: 9px 10px; border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface-2); color: var(--text-primary); font-size: 13px;
  }}
  .filter-field select:focus, .filter-field input:focus {{ outline: none; border-color: var(--accent); }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; padding: 6px 0; }}
  .bar-label {{ width: 220px; flex-shrink: 0; font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .bar-track {{ flex: 1; background: var(--gridline); border-radius: 5px; height: 13px; }}
  .bar-fill {{ background: linear-gradient(90deg, var(--accent-dark), var(--accent)); height: 13px; border-radius: 5px; min-width: 4px; }}
  .bar-value {{ width: 56px; text-align: right; font-size: 13px; color: var(--text-primary); font-weight: 600; font-variant-numeric: tabular-nums; }}
  .empty {{ color: var(--text-muted); }}
  input#search {{
    width: 100%; padding: 10px 12px; margin-bottom: 12px;
    border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface-2); color: var(--text-primary); font-size: 14px;
  }}
  input#search:focus {{ outline: none; border-color: var(--accent); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--gridline); }}
  th {{ color: var(--accent); font-weight: 700; cursor: pointer; user-select: none; white-space: nowrap; font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px; }}
  th:hover {{ color: var(--text-primary); }}
  tbody tr:hover {{ background: var(--surface-2); }}
  .table-scroll {{ max-height: 520px; overflow-y: auto; }}
  .count-note {{ direction: rtl; text-align: right; color: var(--text-muted); font-size: 12px; margin-top: 8px; }}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <div class="logo">
      <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="26" cy="26" r="24" stroke="#f2701c" stroke-width="3"/>
        <path d="M26 2 A24 24 0 0 1 26 50" stroke="#f2701c" stroke-width="3"/>
        <path d="M2 26 H50 M9 12 Q26 26 9 40 M43 12 Q26 26 43 40" stroke="#f2701c" stroke-width="1.6" opacity="0.8"/>
      </svg>
    </div>
    <div>
      <h1>Euro<span class="accent">League</span> Player Stats</h1>
      <p class="subtitle">עונות {season_range} · נוצר ב-{date.today().isoformat()} · סמל מעוצב בהשראת המותג (לא הלוגו הרשמי)</p>
    </div>
  </div>
</header>
<div class="wrap">
  <div class="tiles">
    <div class="tile"><div class="value">{overview['players']}</div><div class="label">שחקנים</div></div>
    <div class="tile"><div class="value">{overview['teams']}</div><div class="label">קבוצות</div></div>
    <div class="tile"><div class="value">{overview['countries']}</div><div class="label">מדינות</div></div>
    <div class="tile"><div class="value">{season_range}</div><div class="label">טווח עונות</div></div>
  </div>

  <section>
    <h2>דירוג לפי סינון חופשי (קבוצה / מדינה / עונה / סטטיסטיקה)</h2>
    <div class="filters">
      <div class="filter-field">
        <label>סטטיסטיקה</label>
        <select id="statFilter"></select>
      </div>
      <div class="filter-field">
        <label>עונה</label>
        <select id="seasonFilter"></select>
      </div>
      <div class="filter-field">
        <label>קבוצה</label>
        <select id="teamFilter"></select>
      </div>
      <div class="filter-field">
        <label>מדינה</label>
        <select id="countryFilter"></select>
      </div>
      <div class="filter-field">
        <label>מינימום משחקים</label>
        <input type="number" id="minGames" value="20" min="0" style="width:80px">
      </div>
    </div>
    <div id="dynamicBars"></div>
    <p class="count-note" id="dynamicNote"></p>
  </section>

  <section>
    <h2>שחקנים לכל מדינה (Top {TOP_COUNTRIES_LIMIT})</h2>
    {countries_bars}
  </section>

  <section>
    <h2>כל השחקנים - חיפוש וסינון חופשי (סיכום קריירה בנקודות)</h2>
    <input type="text" id="search" placeholder="חפש לפי שם / מדינה / קבוצה...">
    <div class="table-scroll">
    <table id="playersTable">
      <thead>
        <tr>
          <th data-col="0">שם</th>
          <th data-col="1">מדינה</th>
          <th data-col="2">קבוצות</th>
          <th data-col="3">עונות</th>
          <th data-col="4">משחקי קריירה</th>
          <th data-col="5">ממוצע נקודות</th>
        </tr>
      </thead>
      <tbody>
        {table_html}
      </tbody>
    </table>
    </div>
    <p class="count-note" id="rowCount"></p>
  </section>
</div>

<script>
  const DATA = {records_json};
  const STAT_LABELS = {stat_labels_json};

  function escapeHtml(s) {{
    return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
  }}

  function fillSelect(id, values, allLabel) {{
    const sel = document.getElementById(id);
    sel.innerHTML = `<option value="">${{allLabel}}</option>` +
      values.map(v => `<option value="${{escapeHtml(v)}}">${{escapeHtml(v)}}</option>`).join('');
  }}

  // אתחול הפילטרים מתוך הנתונים המוטמעים
  const statSel = document.getElementById('statFilter');
  statSel.innerHTML = Object.entries(STAT_LABELS)
    .filter(([key]) => key !== 'gamesPlayed')
    .map(([key, label]) => `<option value="${{key}}">${{escapeHtml(label)}}</option>`).join('');
  statSel.value = 'pointsScored';

  const teams = [...new Set(DATA.map(r => r.team).filter(Boolean))].sort();
  const countries = [...new Set(DATA.map(r => r.country).filter(Boolean))].sort();
  const seasons = [...new Set(DATA.map(r => r.season))].sort();

  fillSelect('teamFilter', teams, 'כל הקבוצות');
  fillSelect('countryFilter', countries, 'כל המדינות');
  document.getElementById('seasonFilter').innerHTML =
    `<option value="ALL">כל הזמנים</option>` + seasons.map(s => `<option value="${{s}}">${{s}}</option>`).join('');

  function renderDynamicBars(items, valueFmt) {{
    const container = document.getElementById('dynamicBars');
    if (!items.length) {{
      container.innerHTML = "<p class='empty'>אין נתונים תואמים לסינון הזה.</p>";
      return;
    }}
    const maxValue = Math.max(...items.map(i => i.value)) || 1;
    container.innerHTML = items.map(i => {{
      const pct = Math.max(2, (i.value / maxValue * 100).toFixed(1));
      const label = escapeHtml(i.player + (i.country ? ` (${{i.country}})` : ''));
      const valueText = valueFmt(i.value);
      return `<div class="bar-row">
        <div class="bar-label">${{label}}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${{pct}}%" title="${{label}}: ${{valueText}}"></div></div>
        <div class="bar-value">${{valueText}}</div>
      </div>`;
    }}).join('');
  }}

  function renderDynamic() {{
    const team = document.getElementById('teamFilter').value;
    const country = document.getElementById('countryFilter').value;
    const season = document.getElementById('seasonFilter').value;
    const stat = document.getElementById('statFilter').value;
    const minGames = parseFloat(document.getElementById('minGames').value) || 0;

    const rows = DATA.filter(r =>
      (!team || r.team === team) &&
      (!country || r.country === country) &&
      (season === 'ALL' || r.season === season)
    );

    let leaderboard;
    if (season === 'ALL') {{
      const byPlayer = {{}};
      rows.forEach(r => {{
        const key = r.player;
        if (!byPlayer[key]) byPlayer[key] = {{player: r.player, country: r.country, weighted: 0, games: 0}};
        const games = r.stats.gamesPlayed || 0;
        const val = r.stats[stat];
        if (val !== undefined && games) {{
          byPlayer[key].weighted += val * games;
          byPlayer[key].games += games;
        }}
      }});
      leaderboard = Object.values(byPlayer)
        .filter(p => p.games >= minGames)
        .map(p => ({{player: p.player, country: p.country, value: p.weighted / p.games}}));
    }} else {{
      leaderboard = rows
        .filter(r => r.stats[stat] !== undefined && (r.stats.gamesPlayed || 0) >= minGames)
        .map(r => ({{player: r.player, country: r.country, value: r.stats[stat]}}));
    }}

    leaderboard.sort((a, b) => b.value - a.value);
    const top = leaderboard.slice(0, 30);

    renderDynamicBars(top, v => v.toFixed(1));
    document.getElementById('dynamicNote').textContent = `${{leaderboard.length}} שחקנים תואמים לסינון (מוצגים עד 30)`;
  }}

  ['teamFilter', 'countryFilter', 'seasonFilter', 'statFilter', 'minGames'].forEach(id => {{
    document.getElementById(id).addEventListener('input', renderDynamic);
    document.getElementById(id).addEventListener('change', renderDynamic);
  }});
  document.getElementById('seasonFilter').value = 'ALL';
  renderDynamic();

  // חיפוש/מיון בטבלה הסטטית (סיכום קריירה בנקודות, כל השחקנים)
  const search = document.getElementById('search');
  const tableRows = Array.from(document.querySelectorAll('#playersTable tbody tr'));
  const rowCount = document.getElementById('rowCount');

  function updateCount() {{
    const visible = tableRows.filter(r => r.style.display !== 'none').length;
    rowCount.textContent = `${{visible}} מתוך ${{tableRows.length}} שחקנים`;
  }}

  search.addEventListener('input', () => {{
    const q = search.value.trim().toLowerCase();
    tableRows.forEach(r => {{
      r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    }});
    updateCount();
  }});

  document.querySelectorAll('#playersTable th').forEach(th => {{
    let asc = true;
    th.addEventListener('click', () => {{
      const col = parseInt(th.dataset.col, 10);
      const tbody = document.querySelector('#playersTable tbody');
      const sorted = tableRows.slice().sort((a, b) => {{
        const cellA = a.children[col];
        const cellB = b.children[col];
        const va = cellA.dataset.sort !== undefined ? parseFloat(cellA.dataset.sort) : cellA.textContent.toLowerCase();
        const vb = cellB.dataset.sort !== undefined ? parseFloat(cellB.dataset.sort) : cellB.textContent.toLowerCase();
        if (va < vb) return asc ? -1 : 1;
        if (va > vb) return asc ? 1 : -1;
        return 0;
      }});
      sorted.forEach(r => tbody.appendChild(r));
      asc = !asc;
    }});
  }});

  updateCount();
</script>
</body>
</html>
"""

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"נוצר {OUTPUT_PATH} - פתח אותו בדפדפן (לחיצה כפולה על הקובץ).")


if __name__ == "__main__":
    main()
