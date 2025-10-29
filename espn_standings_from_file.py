import datetime

INPUT_FILE = "espn_games_2025_26.txt"
OUTPUT_FILE = "espn_standings_2025_26.txt"

teams = {}

def update_team(team, gf, ga, result):
    """Update a team's record"""
    if team not in teams:
        teams[team] = {"W":0, "L":0, "OTL":0, "GF":0, "GA":0, "PTS":0}

    t = teams[team]
    t["GF"] += gf
    t["GA"] += ga

    if result == "win":
        t["W"] += 1
        t["PTS"] += 2
    elif result == "loss":
        t["L"] += 1
    elif result == "otl":
        t["OTL"] += 1
        t["PTS"] += 1


# --- Read the local game file ---
try:
    with open(INPUT_FILE) as f:
        lines = [ln.strip() for ln in f if ln.strip()]
except FileNotFoundError:
    print(f"Error: file '{INPUT_FILE}' not found.")
    exit()

for line in lines:
    parts = line.split()
    if len(parts) < 6:
        continue

    # detect game id
    game_id = parts[0]
    note = ""
    # possible patterns:
    #  id  AWAY score @ HOME score [OT/SO]
    if "@" in parts:
        at_index = parts.index("@")
        try:
            away_abbr = parts[1]
            away_score = int(parts[2])
            home_abbr = parts[at_index + 1]
            home_score = int(parts[at_index + 2])
            if len(parts) > at_index + 3:
                note = parts[at_index + 3].upper()
        except Exception:
            print(f"Skipping malformed line: {line}")
            continue
    else:
        print(f"Skipping missing-@ line: {line}")
        continue

    # Determine winner and handle OTL
    if home_score > away_score:
        # home wins
        if note in ("OT", "SO"):
            update_team(home_abbr, home_score, away_score, "win")
            update_team(away_abbr, away_score, home_score, "otl")
        else:
            update_team(home_abbr, home_score, away_score, "win")
            update_team(away_abbr, away_score, home_score, "loss")
    elif away_score > home_score:
        # away wins
        if note in ("OT", "SO"):
            update_team(away_abbr, away_score, home_score, "win")
            update_team(home_abbr, home_score, away_score, "otl")
        else:
            update_team(away_abbr, away_score, home_score, "win")
            update_team(home_abbr, home_score, away_score, "loss")

# --- Sort standings ---
sorted_teams = sorted(
    teams.items(),
    key=lambda kv: (-kv[1]["PTS"], -kv[1]["W"], -(kv[1]["GF"] - kv[1]["GA"]))
)

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

lines_out = [
    f"NHL STANDINGS (Generated {now})",
    "----------------------------------------------------------",
    f"{'Team':<6}{'W':>4}{'L':>4}{'OTL':>6}{'GF':>6}{'GA':>6}{'PTS':>6}"
]

for team, st in sorted_teams:
    lines_out.append(
        f"{team:<6}{st['W']:>4}{st['L']:>4}{st['OTL']:>6}{st['GF']:>6}{st['GA']:>6}{st['PTS']:>6}"
    )

# --- Write output file ---
with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(lines_out))

print(f"Standings written to {OUTPUT_FILE}")
