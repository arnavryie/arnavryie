import json
import os
import subprocess
import sys
from datetime import datetime

USERNAME = "arnavryie"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_SVG = os.path.join(REPO_ROOT, "assets", "streak-stats.svg")

def query_graphql(query):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        import urllib.request
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "User-Agent": "StreakGenerator"}
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    else:
        out = subprocess.check_output(["gh", "api", "graphql", "-f", f"query={query}"])
        return json.loads(out)

def get_stats():
    # 1. Total all-time contributions
    total_contributions = 0
    now_year = datetime.now().year
    for year in range(2023, now_year + 1):
        q = f'''
        query {{
          user(login: "{USERNAME}") {{
            contributionsCollection(from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z") {{
              contributionCalendar {{
                totalContributions
              }}
            }}
          }}
        }}
        '''
        res = query_graphql(q)
        cnt = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        total_contributions += cnt

    # 2. Get day-by-day contribution history for the last 1 year to compute streaks
    q_days = f'''
    query {{
      user(login: "{USERNAME}") {{
        contributionsCollection {{
          contributionCalendar {{
            weeks {{
              contributionDays {{
                date
                contributionCount
              }}
            }}
          }}
        }}
      }}
    }}
    '''
    res_days = query_graphql(q_days)
    weeks = res_days["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append(d)
    
    # Sort by date
    days.sort(key=lambda x: x["date"])
    
    # Calculate longest streak & current streak
    # Filter up to today's date
    today_str = datetime.now().strftime("%Y-%m-%d")
    relevant_days = [d for d in days if d["date"] <= today_str]
    
    streaks = []
    curr_s = []
    for d in relevant_days:
        if d["contributionCount"] > 0:
            curr_s.append(d["date"])
        else:
            if curr_s:
                streaks.append(curr_s)
                curr_s = []
    if curr_s:
        streaks.append(curr_s)
        
    longest_streak = 0
    longest_start = ""
    longest_end = ""
    for s in streaks:
        if len(s) > longest_streak:
            longest_streak = len(s)
            longest_start = s[0]
            longest_end = s[-1]
            
    # Current streak: if the last streak includes today or yesterday
    current_streak = 0
    current_start = ""
    current_end = ""
    if streaks:
        last_streak = streaks[-1]
        # check if last day is today or yesterday
        last_day = last_streak[-1]
        current_streak = len(last_streak)
        current_start = last_streak[0]
        current_end = last_streak[-1]

    def fmt_date(d_str):
        if not d_str:
            return ""
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        return dt.strftime("%b %-d")
        
    return {
        "total": f"{total_contributions:,}",
        "total_range": "Nov 29, 2023 - Present",
        "current_streak": str(current_streak),
        "current_range": f"{fmt_date(current_start)} - {fmt_date(current_end)}",
        "longest_streak": str(longest_streak),
        "longest_range": f"{fmt_date(longest_start)} - {fmt_date(longest_end)}"
    }

def render_svg(stats):
    svg = f'''<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'
            style='isolation: isolate' viewBox='0 0 495 195' width='495px' height='195px' direction='ltr'>
    <style>
        @keyframes currstreak {{
            0% {{ font-size: 3px; opacity: 0.2; }}
            80% {{ font-size: 34px; opacity: 1; }}
            100% {{ font-size: 28px; opacity: 1; }}
        }}
        @keyframes fadein {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
    </style>
    <defs>
        <clipPath id='outer_rectangle'>
            <rect width='495' height='195' rx='4.5'/>
        </clipPath>
        <mask id='mask_out_ring_behind_fire'>
            <rect width='495' height='195' fill='white'/>
            <ellipse id='mask-ellipse' cx='247.5' cy='32' rx='13' ry='18' fill='black'/>
        </mask>
    </defs>
    <g clip-path='url(#outer_rectangle)'>
        <g style='isolation: isolate'>
            <rect stroke='none' fill='#06070b' rx='4.5' x='0.5' y='0.5' width='494' height='194'/>
        </g>
        <g style='isolation: isolate'>
            <line x1='165' y1='28' x2='165' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#8b5cff' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
            <line x1='330' y1='28' x2='330' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#8b5cff' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
        </g>
        <g style='isolation: isolate'>
            <!-- Total Contributions big number -->
            <g transform='translate(82.5, 48)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#f4f3fb' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                    {stats['total']}
                </text>
            </g>

            <!-- Total Contributions label -->
            <g transform='translate(82.5, 84)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#8a8aa3' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.7s'>
                    Total Contributions
                </text>
            </g>

            <!-- Total Contributions range -->
            <g transform='translate(82.5, 114)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#8a8aa3' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.8s'>
                    {stats['total_range']}
                </text>
            </g>
        </g>
        <g style='isolation: isolate'>
            <!-- Current Streak label -->
            <g transform='translate(247.5, 108)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#19e6ff' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='700' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                    Current Streak
                </text>
            </g>

            <!-- Current Streak range -->
            <g transform='translate(247.5, 145)'>
                <text x='0' y='21' stroke-width='0' text-anchor='middle' fill='#8a8aa3' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                    {stats['current_range']}
                </text>
            </g>

            <!-- Ring around number -->
            <g mask='url(#mask_out_ring_behind_fire)'>
                <circle cx='247.5' cy='71' r='40' fill='none' stroke='#ff2bd6' stroke-width='5' style='opacity: 0; animation: fadein 0.5s linear forwards 0.4s'></circle>
            </g>
            <!-- Fire icon -->
            <g transform='translate(247.5, 19.5)' stroke-opacity='0' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                <path d='M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z' fill='none'/>
                <path d='M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z' fill='#19e6ff' stroke-opacity='0'/>
            </g>

            <!-- Current Streak big number -->
            <g transform='translate(247.5, 48)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#f4f3fb' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='animation: currstreak 0.6s linear forwards'>
                    {stats['current_streak']}
                </text>
            </g>

        </g>
        <g style='isolation: isolate'>
            <!-- Longest Streak big number -->
            <g transform='translate(412.5, 48)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#f4f3fb' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.2s'>
                    {stats['longest_streak']}
                </text>
            </g>

            <!-- Longest Streak label -->
            <g transform='translate(412.5, 84)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#8a8aa3' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.3s'>
                    Longest Streak
                </text>
            </g>

            <!-- Longest Streak range -->
            <g transform='translate(412.5, 114)'>
                <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#8a8aa3' stroke='none' font-family='\"Segoe UI\", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.4s'>
                    {stats['longest_range']}
                </text>
            </g>
        </g>
    </g>
</svg>'''
    return svg

if __name__ == "__main__":
    print("Calculating live stats from GitHub API...")
    stats = get_stats()
    print("Stats computed:", stats)
    svg = render_svg(stats)
    with open(OUTPUT_SVG, "w") as f:
        f.write(svg.strip())
    print(f"Updated {OUTPUT_SVG} successfully.")
