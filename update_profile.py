import os
import json
import urllib.request
import calendar
from datetime import date, datetime, timezone
import html

USER = "SamuelIVX"
JOINED_YEAR = 2022
W = 75

ART = """
       .-----------------.
      /                 /|
     /                 / |
    /                 /  |
   /                 /   |
  .-----------------.    |
  |                 |    |
  |  >_             |    |
  |                 |    |
  |                 |   /
  |                 |  /
  |                 | /
  '-----------------'/
         ||||
         ||||
      ___||||___
"""

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
PRIV_TOKEN = os.environ.get("ACCESS_TOKEN") or TOKEN

def gh(url, payload=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token or TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read() or "{}")

def graphql(query, variables=None, token=None):
    if not (token or TOKEN):
        return {"user": {}} # fallback for local run
    try:
        _, resp = gh("https://api.github.com/graphql", {"query": query, "variables": variables or {}}, token)
        if resp.get("errors"):
            print("GraphQL Errors:", resp["errors"])
            return {"user": {}}
        return resp["data"]
    except Exception as e:
        print("GraphQL request failed:", e)
        return {"user": {}}

def age(b, t):
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    if t.day >= b.day:
        days = t.day - b.day
    else:
        pm_year, pm = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        days = calendar.monthrange(pm_year, pm)[1] - b.day + t.day
    return years, months, days

def fetch_stats():
    if not TOKEN:
        # Dummy data for local previews without tokens
        return {
            "followers": 10, "repos": 15, "contributed": 5, "stars": 20, "commits": 1200,
            "loc_add": 50000, "loc_del": 20000, "loc": 30000
        }

    yr_aliases = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for y in range(JOINED_YEAR, datetime.now(timezone.utc).year + 1)
    )
    contrib = graphql(f'query {{ user(login: "{USER}") {{ {yr_aliases} }} }}')["user"]
    if not contrib: return { "followers": 0, "repos": 0, "contributed": 0, "stars": 0, "commits": 0, "loc_add": 0, "loc_del": 0, "loc": 0 }
    commits = sum(
        v["totalCommitContributions"] + v["restrictedContributionsCount"]
        for v in contrib.values() if v
    )
    u = graphql(f"""
    query {{
      user(login: "{USER}") {{
        id
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER) {{
          totalCount
          nodes {{ name stargazerCount isFork }}
        }}
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
          totalCount
        }}
      }}
    }}""", token=PRIV_TOKEN)["user"]
    if not u: return { "followers": 0, "repos": 0, "contributed": 0, "stars": 0, "commits": 0, "loc_add": 0, "loc_del": 0, "loc": 0 }
    
    stats = {
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "commits": commits,
    }
    stats.update(loc([n["name"] for n in u["repositories"]["nodes"] if not n["isFork"]], u["id"]))
    return stats

LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      }
    } } }
  }
}"""

def loc(repo_names, user_id):
    add = rem = 0
    if not PRIV_TOKEN:
        return {"loc_add": 0, "loc_del": 0, "loc": 0}
    for name in repo_names:
        cursor = None
        try:
            while True:
                resp = graphql(LOC_QUERY, {"owner": USER, "name": name, "id": user_id, "cursor": cursor}, token=PRIV_TOKEN)
                if not resp or "repository" not in resp or not resp["repository"]["defaultBranchRef"]:
                    break
                ref = resp["repository"]["defaultBranchRef"]
                if not ref: break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    return {"loc_add": add, "loc_del": rem, "loc": add - rem}

PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "art": "#8b949e", "h": "#58a6ff",
             "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58", "g": "#3fb950", "r": "#f85149"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "art": "#57606a", "h": "#0969da",
              "k": "#953800", "v": "#24292f", "d": "#afb8c1", "g": "#1a7f37", "r": "#cf222e"},
}

def kv(key, val, width=W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]

def kv2(k1, v1, k2, v2):
    left = kv(k1, v1, 30)
    return left + [(" | ", "d")] + kv(k2, v2, 23)

def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (W - len(label)), "d")]

def info_lines(s):
    n = lambda x: f"{x:,}"
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (W - len(USER) - 8), "d")],
        [],
        kv("OS", "macOS, Fedora KDE"),
        kv("Education", "BS Computer Science + Math Minor"),
        kv("School", "College of Staten Island"),
        kv("Role", "Software Engineering Intern"),
        kv("IDE", "Cursor, VS Code"),
        [],
        kv("Languages.Programming", "TypeScript, Java, C++, Python"),
        kv("Stack.Web", "Next.js, React, Tailwind, Supabase"),
        kv("Hobbies", "PC Building, Manga, Gaming"),
        [],
        rule("Contact"),
        kv("Portfolio", "samuelivx.github.io"),
        kv("LinkedIn", "in/samuelhernandezcs"),
        [],
        rule("GitHub Stats"),
        kv2("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}", "Stars", n(s["stars"])),
        kv2("Commits", n(s["commits"]), "Followers", n(s["followers"])),
        [("Lines of Code: ", "k"), (n(s["loc"]), "v"), (" ( ", "d"),
         (n(s["loc_add"]) + "++", "g"), (", ", "d"), (n(s["loc_del"]) + "--", "r"), (" )", "d")],
    ]

def render(mode, stats):
    p = PALETTES[mode]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="420" viewBox="0 0 840 420" '
        f'font-family="Consolas, Menlo, monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="839" height="419" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    for i, line in enumerate(ART.strip("\\n").split("\\n")):
        out.append(f'<text x="25" y="{40 + i * 15}" fill="{p["art"]}" xml:space="preserve">{html.escape(line)}</text>')
    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(f'<text x="310" y="{45 + i * 21}" xml:space="preserve">{spans}</text>')
    out.append("</svg>")
    return "\\n".join(out)

if __name__ == "__main__":
    stats = fetch_stats()
    print("stats:", stats)
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
