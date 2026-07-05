import json
from pathlib import Path
from datetime import datetime

INPUT_JSON = "cleaneddata.json"
OUTPUT_HTML = "index.html"

# --- Timestamp logic ---
now = datetime.now()
formatted_date = now.strftime("%A, %d %B %H:%M")

# --- Week number logic ---
current_week = now.isocalendar()[1]
previous_week = current_week - 1
previous_week_folder = f"week_{previous_week}_log"
previous_week_json = f"{previous_week_folder}/cleaneddata.json"

TIER_COLORS = {
    "master": "#ff4d4d",
    "diamond": "#3fa9ff",
    "platinum": "#b8c2cc",
    "gold": "#f5c542",
    "silver": "#bcbcbc",
    "bronze": "#c57a44",
}

TIER_ICONS = {
    "master": "👑",
    "diamond": "💎",
    "platinum": "🔷",
    "gold": "🥇",
    "silver": "🥈",
    "bronze": "🥉",
}

def fmt_number(value):
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"

# Load current data
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    current_data = json.load(f)

# Load previous week data if it exists
previous_data = None
if Path(previous_week_json).exists():
    with open(previous_week_json, "r", encoding="utf-8") as f:
        previous_data = json.load(f)

mu = current_data["mu"]
members = current_data["members"]

# Helper: get previous rank for a member and stat
def get_previous_rank(member_username, stat_key):
    if not previous_data:
        return None
    for prev_member in previous_data["members"]:
        if prev_member["username"] == member_username:
            return prev_member["rankings"][stat_key]["rank"]
    return None

# Helper: rank evolution string
def get_rank_evolution(current_rank, previous_rank):
    if previous_rank is None:
        return "New"
    if current_rank < previous_rank:
        return f"#{previous_rank} → #{current_rank} (↑{previous_rank - current_rank})"
    elif current_rank > previous_rank:
        return f"#{previous_rank} → #{current_rank} (↓{current_rank - previous_rank})"
    else:
        return f"#{previous_rank} → #{current_rank}"

# Helper: diff between two values
def calculate_diff(current_value, previous_value):
    if previous_value is None:
        return None
    return current_value - previous_value

# Build MU stat card
def build_stat_card(title, value, rank, tier, diff=None, previous_rank=None):
    diff_html = ""
    if diff is not None:
        diff_color = "#4ade80" if diff >= 0 else "#f87171"
        diff_symbol = "+" if diff >= 0 else ""
        diff_html = f'<div class="stat-diff" style="color:{diff_color}">{diff_symbol}{fmt_number(diff)}</div>'

    rank_evolution_html = ""
    if previous_rank is not None:
        evolution = get_rank_evolution(rank, previous_rank)
        rank_evolution_html = f'<div class="stat-rank-evolution">{evolution}</div>'

    return f"""
    <div class="stat-card {tier}">
        <div class="stat-title">{title}</div>
        <div class="stat-value">{fmt_number(value)}</div>
        {diff_html}
        {rank_evolution_html}
        <div class="stat-rank">
            {TIER_ICONS.get(tier,'')} Rank #{rank}
        </div>
    </div>
    """

# Build standard ranking table
def build_table(title, ranking, stat_key):
    # Build a lookup: username -> previous internal position in this same ranking
    prev_positions = {}
    if previous_data:
        prev_sorted = sorted(
            previous_data["members"],
            key=lambda m: m["rankings"][stat_key]["value"],
            reverse=True,
        )
        for i, m in enumerate(prev_sorted, start=1):
            prev_positions[m["username"]] = i

    rows = []
    for position, member in enumerate(ranking, start=1):
        data = member["rankings"][stat_key]
        value = data["value"]
        tier = data["tier"]
        current_rank = data["rank"]
        color = TIER_COLORS.get(tier, "#999999")
        icon = TIER_ICONS.get(tier, "🏅")

        previous_value = None
        if previous_data:
            for prev_member in previous_data["members"]:
                if prev_member["username"] == member["username"]:
                    previous_value = prev_member["rankings"][stat_key]["value"]
                    break
        diff = calculate_diff(value, previous_value)

        previous_rank = get_previous_rank(member["username"], stat_key)
        rank_evolution = get_rank_evolution(current_rank, previous_rank)

        # Internal position change badge (e.g. 6→3)
        prev_pos = prev_positions.get(member["username"])
        if prev_pos is None:
            pos_badge = '<span class="pos-new">New</span>'
        elif prev_pos == position:
            pos_badge = '<span class="pos-same">—</span>'
        elif prev_pos > position:
            pos_badge = f'<span class="pos-up">{prev_pos}→{position}</span>'
        else:
            pos_badge = f'<span class="pos-down">{prev_pos}→{position}</span>'

        diff_html = ""
        if diff is not None:
            diff_color = "#4ade80" if diff >= 0 else "#f87171"
            diff_symbol = "+" if diff >= 0 else ""
            diff_html = f'<td class="diff-col" style="color:{diff_color}">{diff_symbol}{fmt_number(diff)}</td>'

        rows.append(f"""
            <tr>
                <td class="rank-col">#{position} {pos_badge}</td>
                <td>
                    <div class="member">
                        <img class="avatar" src="{member['avatarUrl']}" alt="{member['username']}">
                        <div class="member-info">
                            <div class="member-name">{member['username']}</div>
                            <div class="member-level">Level {member['level']}</div>
                        </div>
                    </div>
                </td>
                <td class="value-col">{fmt_number(value)}</td>
                <td class="rank-evolution-col">{rank_evolution}</td>
                {diff_html}
                <td><span class="tier" style="background:{color};">{icon} {tier.title()}</span></td>
            </tr>
        """)

    return f"""
    <div class="ranking-card">
        <div class="ranking-title">{title}</div>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Member</th>
                    <th>Value</th>
                    <th>Rank Evolution</th>
                    <th>Diff</th>
                    <th>Tier</th>
                </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
    """

# Build roster change panels (new members / departed members)
def build_roster_changes(current_members, prev_members):
    if not prev_members:
        return ""

    current_usernames = {m["username"] for m in current_members}
    prev_usernames    = {m["username"] for m in prev_members}

    new_members      = [m for m in current_members if m["username"] not in prev_usernames]
    departed_members = [m for m in prev_members    if m["username"] not in current_usernames]

    def member_row(m, badge_color, badge_label):
        return f"""
        <div class="roster-row">
            <img class="avatar" src="{m['avatarUrl']}" alt="{m['username']}">
            <div class="member-info">
                <div class="member-name">{m['username']}</div>
                <div class="member-level">Level {m['level']}</div>
            </div>
            <span class="roster-badge" style="background:{badge_color};">{badge_label}</span>
        </div>
        """

    def build_panel(title, icon, members_list, badge_color, badge_label, empty_msg):
        if members_list:
            rows_html = "".join(member_row(m, badge_color, badge_label) for m in members_list)
        else:
            rows_html = f'<div class="roster-empty">{empty_msg}</div>'
        return f"""
        <div class="ranking-card">
            <div class="ranking-title">{icon} {title} <span class="roster-count">({len(members_list)})</span></div>
            <div class="roster-list">{rows_html}</div>
        </div>
        """

    new_panel = build_panel(
        "New Recruits", "🟢", new_members,
        "#166534", "Joined",
        "No new members this week."
    )
    departed_panel = build_panel(
        "Departed Members", "🔴", departed_members,
        "#7f1d1d", "Left",
        "No departures this week."
    )

    return f"""
    <div class="section-label">Roster Changes</div>
    <div class="rankings-two-col">
        {new_panel}
        {departed_panel}
    </div>
    """

# ── MU stat cards ──────────────────────────────────────────────────────────────
mu_weekly_damage = mu["rankings"]["muWeeklyDamages"]
mu_total_damage  = mu["rankings"]["muDamages"]
mu_bounty        = mu["rankings"]["muBounty"]
mu_reputation    = mu["rankings"]["muReputation"]

mu_weekly_damage_diff = mu_total_damage_diff = mu_bounty_diff = mu_reputation_diff = None
mu_weekly_damage_prev_rank = mu_total_damage_prev_rank = mu_bounty_prev_rank = mu_reputation_prev_rank = None

if previous_data:
    prev_mu = previous_data["mu"]
    mu_weekly_damage_diff      = calculate_diff(mu_weekly_damage["value"], prev_mu["rankings"]["muWeeklyDamages"]["value"])
    mu_total_damage_diff       = calculate_diff(mu_total_damage["value"],  prev_mu["rankings"]["muDamages"]["value"])
    mu_bounty_diff             = calculate_diff(mu_bounty["value"],        prev_mu["rankings"]["muBounty"]["value"])
    mu_reputation_diff         = calculate_diff(mu_reputation["value"],    prev_mu["rankings"]["muReputation"]["value"])
    mu_weekly_damage_prev_rank = prev_mu["rankings"]["muWeeklyDamages"]["rank"]
    mu_total_damage_prev_rank  = prev_mu["rankings"]["muDamages"]["rank"]
    mu_bounty_prev_rank        = prev_mu["rankings"]["muBounty"]["rank"]
    mu_reputation_prev_rank    = prev_mu["rankings"]["muReputation"]["rank"]

stats_html = "".join([
    build_stat_card("Weekly Damage", mu_weekly_damage["value"], mu_weekly_damage["rank"], mu_weekly_damage["tier"],
                    diff=mu_weekly_damage_diff, previous_rank=mu_weekly_damage_prev_rank),
    build_stat_card("Total Damage",  mu_total_damage["value"],  mu_total_damage["rank"],  mu_total_damage["tier"],
                    diff=mu_total_damage_diff,  previous_rank=mu_total_damage_prev_rank),
    build_stat_card("Bounty",        mu_bounty["value"],        mu_bounty["rank"],        mu_bounty["tier"],
                    diff=mu_bounty_diff,        previous_rank=mu_bounty_prev_rank),
    build_stat_card("Reputation",    mu_reputation["value"],    mu_reputation["rank"],    mu_reputation["tier"],
                    diff=mu_reputation_diff,    previous_rank=mu_reputation_prev_rank),
])

# ── Sort rankings ──────────────────────────────────────────────────────────────
weekly_damage_ranking = sorted(members, key=lambda m: m["rankings"]["weeklyUserDamages"]["value"], reverse=True)
total_damage_ranking  = sorted(members, key=lambda m: m["rankings"]["userDamages"]["value"],       reverse=True)
bounty_ranking        = sorted(members, key=lambda m: m["rankings"]["userBounty"]["value"],        reverse=True)
wealth_ranking        = sorted(members, key=lambda m: m["rankings"]["userWealth"]["value"],        reverse=True)

# ── Roster changes ─────────────────────────────────────────────────────────────
roster_changes_html = build_roster_changes(members, previous_data["members"] if previous_data else None)

# ── Navigation links — fill these manually ────────────────────────────────────
BASE_URL          = "https://koifeurops.github.io/Warera-Spectre-Log"
PREVIOUS_WEEK_URL = f"{BASE_URL}/Week-{current_week - 1}.html"
NEXT_WEEK_URL     = f"{BASE_URL}/Week-{current_week + 1}.html"

html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{mu['name']} Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0b1220; color:white; font-family:Arial,sans-serif; padding:24px; }}
.container {{ max-width:1900px; margin:auto; }}

.mu-header {{
    display:flex; align-items:center; justify-content:space-between;
    gap:20px; padding:24px; margin-bottom:24px;
    background:#131d31; border:1px solid #25324d; border-radius:18px;
}}
.mu-header-left {{ display:flex; align-items:center; gap:20px; }}
.mu-header img {{ width:96px; height:96px; border-radius:50%; }}
.mu-name {{ font-size:2rem; font-weight:bold; }}
.mu-subtitle {{ color:#94a3b8; margin-top:6px; }}
.generated-at {{ color:#94a3b8; font-size:0.9rem; text-align:right; }}

.stats {{
    display:grid; grid-template-columns:repeat(4,1fr);
    gap:18px; margin-bottom:24px;
}}
.stat-card {{
    background:#131d31; border:1px solid #25324d;
    border-radius:16px; padding:20px;
}}
.stat-title {{ color:#94a3b8; font-size:.9rem; }}
.stat-value {{ font-size:1.8rem; font-weight:bold; margin-top:10px; }}
.stat-rank {{ margin-top:8px; color:#cbd5e1; }}
.stat-diff {{ font-size:0.9rem; margin-top:6px; }}
.stat-rank-evolution {{ font-size:0.8rem; color:#94a3b8; margin-top:4px; }}

.master   {{ border-left:6px solid #ff4d4d; }}
.diamond  {{ border-left:6px solid #3fa9ff; }}
.platinum {{ border-left:6px solid #b8c2cc; }}
.gold     {{ border-left:6px solid #f5c542; }}
.silver   {{ border-left:6px solid #bcbcbc; }}
.bronze   {{ border-left:6px solid #c57a44; }}

.section-label {{
    color:#94a3b8; font-size:0.8rem; text-transform:uppercase;
    letter-spacing:0.08em; margin-bottom:10px; margin-top:24px; padding-left:4px;
}}
.rankings, .rankings-two-col {{
    display:grid; grid-template-columns:repeat(2,1fr); gap:20px;
}}
.ranking-card {{
    background:#131d31; border:1px solid #25324d;
    border-radius:18px; overflow:hidden;
}}
.ranking-title {{
    background:#1a2740; padding:18px;
    font-weight:bold; font-size:1.1rem;
}}
.roster-count {{ font-weight:400; color:#94a3b8; font-size:0.9rem; }}

table {{ width:100%; border-collapse:collapse; }}
thead th {{ position:sticky; top:0; background:#1f2f4d; }}
th {{ text-align:left; padding:12px; }}
td {{ padding:12px; border-bottom:1px solid #202f49; }}
tbody tr:hover {{ background:rgba(255,255,255,.03); }}

.member {{ display:flex; align-items:center; gap:12px; }}
.avatar {{
    width:42px; height:42px; border-radius:50%;
    object-fit:cover; border:2px solid #334155;
}}
.member-info {{ display:flex; flex-direction:column; }}
.member-name {{ font-weight:600; }}
.member-level {{ color:#94a3b8; font-size:.85rem; }}
.tier {{
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 10px; border-radius:999px;
    color:white; font-size:.85rem; font-weight:bold;
}}
.rank-col {{ width:110px; white-space:nowrap; }}
.pos-up   {{ font-size:0.72rem; font-weight:700; color:#4ade80; background:rgba(74,222,128,0.12); padding:2px 6px; border-radius:6px; margin-left:4px; }}
.pos-down {{ font-size:0.72rem; font-weight:700; color:#f87171; background:rgba(248,113,113,0.12); padding:2px 6px; border-radius:6px; margin-left:4px; }}
.pos-same {{ font-size:0.72rem; color:#64748b; margin-left:4px; }}
.pos-new  {{ font-size:0.72rem; font-weight:700; color:#60a5fa; background:rgba(96,165,250,0.12); padding:2px 6px; border-radius:6px; margin-left:4px; }}
.value-col {{ font-weight:bold; }}
.rank-evolution-col {{ font-weight:bold; color:#94a3b8; font-size:0.9rem; }}
.diff-col {{ font-weight:bold; }}

/* Roster changes */
.roster-list {{ padding:12px 16px; display:flex; flex-direction:column; gap:10px; }}
.roster-row {{
    display:flex; align-items:center; gap:12px;
    padding:10px 12px; border-radius:10px;
    background:#0f1929; border:1px solid #1e2f48;
}}
.roster-badge {{
    margin-left:auto; padding:4px 12px;
    border-radius:999px; font-size:0.8rem; font-weight:bold; color:white;
}}
.roster-empty {{
    padding:20px 16px; color:#94a3b8; font-size:0.9rem; text-align:center;
}}

/* Navigation buttons */
.nav-buttons {{
    display:flex; justify-content:space-between; align-items:center;
    gap:16px; margin-top:32px; padding-top:24px; border-top:1px solid #25324d;
}}
.nav-btn {{
    display:inline-flex; align-items:center; gap:10px;
    padding:14px 28px; background:#131d31; border:1px solid #25324d;
    border-radius:12px; color:white; font-size:1rem; font-weight:600;
    text-decoration:none; cursor:pointer;
    transition:background 0.18s, border-color 0.18s, transform 0.12s;
}}
.nav-btn:hover {{ background:#1a2740; border-color:#3fa9ff; transform:translateY(-2px); }}
.nav-btn:active {{ transform:translateY(0); }}
.nav-btn-prev::before {{ content:"←"; font-size:1.1rem; }}
.nav-btn-next::after  {{ content:"→"; font-size:1.1rem; }}
.nav-btn-disabled {{ opacity:0.35; pointer-events:none; }}

@media(max-width:1400px) {{ .rankings, .rankings-two-col {{ grid-template-columns:1fr; }} }}
@media(max-width:900px)  {{ .stats {{ grid-template-columns:repeat(2,1fr); }} }}
@media(max-width:600px)  {{
    .stats {{ grid-template-columns:1fr; }}
    .mu-header {{ flex-direction:column; text-align:center; }}
    .nav-buttons {{ flex-direction:column; }}
    .nav-btn {{ width:100%; justify-content:center; }}
}}
</style>
</head>
<body>
<div class="container">

    <!-- Header -->
    <div class="mu-header">
        <div class="mu-header-left">
            <img src="{mu['avatarUrl']}">
            <div>
                <div class="mu-name">{mu['name']}</div>
                <div class="mu-subtitle">Guild Dashboard</div>
            </div>
        </div>
        <div class="generated-at">Generated: {formatted_date}</div>
    </div>

    <!-- MU Stat Cards -->
    <div class="stats">{stats_html}</div>

    <!-- Standard Rankings -->
    <div class="section-label">Standard Rankings</div>
    <div class="rankings">
        {build_table("Weekly Damage Ranking", weekly_damage_ranking, "weeklyUserDamages")}
        {build_table("Total Damage Ranking",  total_damage_ranking,  "userDamages")}
        {build_table("Bounty Ranking",        bounty_ranking,        "userBounty")}
        {build_table("Wealth Ranking",        wealth_ranking,        "userWealth")}
    </div>

    <!-- Roster Changes -->
    {roster_changes_html if roster_changes_html else ""}

    <!-- Navigation Buttons -->
    <div class="nav-buttons">
        <a href="{PREVIOUS_WEEK_URL}" class="nav-btn nav-btn-prev">Semaine dernière</a>
        <a href="{NEXT_WEEK_URL}"     class="nav-btn nav-btn-next">Semaine prochaine</a>
    </div>

</div>
</body>
</html>
"""

Path(OUTPUT_HTML).write_text(html, encoding="utf-8")
print(f"Generated {OUTPUT_HTML}")
