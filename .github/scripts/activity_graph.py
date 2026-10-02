"""Gera um gráfico SVG (estilo neon) com as contribuições dos últimos 30 dias."""
import datetime as dt
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "Jumendess")
TOKEN = os.environ["GITHUB_TOKEN"]
DIAS = 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity-graph.svg"

hoje = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
inicio = hoje - dt.timedelta(days=DIAS - 1)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""
payload = json.dumps({
    "query": query,
    "variables": {"login": USER, "from": inicio.isoformat(), "to": (hoje + dt.timedelta(days=1)).isoformat()},
}).encode()
req = urllib.request.Request(
    "https://api.github.com/graphql", data=payload,
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
dados = json.load(urllib.request.urlopen(req))
semanas = dados["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
contagem = {d["date"]: d["contributionCount"] for w in semanas for d in w["contributionDays"]}

dias = [(inicio + dt.timedelta(days=i)).date() for i in range(DIAS)]
valores = [contagem.get(d.isoformat(), 0) for d in dias]

W, H = 900, 300
ML, MR, MT, MB = 50, 25, 60, 45
pw, ph = W - ML - MR, H - MT - MB
vmax = max(max(valores), 4)
x = lambda i: ML + pw * i / (DIAS - 1)
y = lambda v: MT + ph - ph * v / vmax

pontos = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(valores))
area = f"M{x(0):.1f},{MT + ph} L" + " L".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(valores)) + f" L{x(DIAS - 1):.1f},{MT + ph} Z"

grade = []
for k in range(5):
    v = vmax * k / 4
    yy = y(v)
    grade.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{W - MR}" y2="{yy:.1f}" class="grid"/>')
    grade.append(f'<text x="{ML - 10}" y="{yy + 4:.1f}" class="lbl" text-anchor="end">{round(v)}</text>')
for i in range(0, DIAS, 5):
    grade.append(f'<text x="{x(i):.1f}" y="{H - 18}" class="lbl" text-anchor="middle">{dias[i].strftime("%d/%m")}</text>')

circulos = "".join(
    f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="{4 if v else 2.5}" class="pt" style="animation-delay:{i * 0.04:.2f}s"><title>{dias[i].strftime("%d/%m")}: {v} contribuições</title></circle>'
    for i, v in enumerate(valores)
)
total = sum(valores)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#00E5FF" stop-opacity=".45"/>
    <stop offset="1" stop-color="#00E5FF" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>
  .bg {{ fill:#020617 }}
  .grid {{ stroke:#0E2A44; stroke-width:1; stroke-dasharray:3 4 }}
  .lbl {{ fill:#5B7A99; font:12px 'JetBrains Mono',monospace }}
  .title {{ fill:#E6FBFF; font:600 18px 'JetBrains Mono',monospace }}
  .sub {{ fill:#00E5FF; font:13px 'JetBrains Mono',monospace }}
  .line {{ fill:none; stroke:#00E5FF; stroke-width:2.5; stroke-linejoin:round; filter:url(#glow);
           stroke-dasharray:3000; stroke-dashoffset:3000; animation:draw 2.2s ease-out forwards }}
  .area {{ fill:url(#fill); opacity:0; animation:fade 1.2s .8s forwards }}
  .pt {{ fill:#E6FBFF; stroke:#00E5FF; stroke-width:1.5; opacity:0; animation:fade .4s forwards }}
  @keyframes draw {{ to {{ stroke-dashoffset:0 }} }}
  @keyframes fade {{ to {{ opacity:1 }} }}
</style>
<rect class="bg" width="{W}" height="{H}" rx="14"/>
<text x="{ML}" y="32" class="title">&gt; Atividade no GitHub</text>
<text x="{W - MR}" y="32" class="sub" text-anchor="end">{total} contribuições · últimos {DIAS} dias</text>
{''.join(grade)}
<path d="{area}" class="area"/>
<polyline points="{pontos}" class="line"/>
{circulos}
</svg>
"""
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"OK: {OUT} ({total} contribuições)")
