"""Build docs/index.html: a single self-contained dashboard page.

All numbers are embedded from results/ at build time (no hand-typed values),
and the page loads nothing from the network, so it works on GitHub Pages or
opened straight from disk. ``tests/test_dashboard.py`` checks the embedded
numbers against metrics.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .scoring import nation_contributions

REPO_URL = "https://github.com/RidhimaGupta4/glasgow2026-forecast-postmortem"
FORECASTS = ["B1", "B1p", "B2"]


def build_payload(metrics: dict, out_dir: Path) -> dict:
    t = Path(out_dir) / "tables"
    scores = pd.read_csv(t / "scores.csv")
    diffs = pd.read_csv(t / "paired_differences.csv")
    ranks = pd.read_csv(t / "ranks_by_nation.csv").set_index("nation")
    hist = pd.read_csv(t / "historical_carry_forward.csv")
    prog = pd.read_csv(t / "programme_effect.csv", index_col=0)
    tiers = pd.read_csv(t / "tiers.csv").set_index("nation")["tier"]

    truth = ranks["true_rank"]
    nations = []
    contrib = {f: nation_contributions(ranks[f"{f}_rank"], truth) for f in FORECASTS}
    for n, row in ranks.iterrows():
        nations.append({
            "nation": n,
            "gold": int(row["gold"]), "silver": int(row["silver"]), "bronze": int(row["bronze"]),
            "true": int(row["true_rank"]),
            "tier": int(tiers[n]),
            **{f: int(row[f"{f}_rank"]) for f in FORECASTS},
            **{f"{f}_c": int(contrib[f].loc[n, "concordant"]) for f in FORECASTS},
            **{f"{f}_d": int(contrib[f].loc[n, "discordant"]) for f in FORECASTS},
        })

    tier_rows = {}
    for f in FORECASTS:
        tt = pd.read_csv(t / f"tiers_{f}.csv")
        tier_rows[f] = [{"pair_type": r.pair_type, "pairs": int(r.pairs), "tied": float(r.share_tied_in_truth),
                         "tau_within": float(r.tau_within), "lost": float(r.score_lost)} for r in tt.itertuples()]

    hist_rows = [{"target": int(r.target_games), "tau": float(r.tau), "ceiling": float(r.ceiling)}
                 for r in hist.itertuples()]
    b1 = scores.set_index("forecast").loc["B1"]
    hist_rows.append({"target": 2026, "tau": float(b1["tau"]), "ceiling": float(metrics["tau_ceiling"])})

    top = prog.sort_values("golds_2022_dropped_sports", ascending=False).head(12)
    prog_rows = [{"nation": n, "all": int(r.golds_2022_all_sports), "kept": int(r.golds_2022_2026_sports),
                  "actual": int(ranks.loc[n, "gold"]), "b1": int(ranks.loc[n, "B1_rank"]),
                  "b1p": int(ranks.loc[n, "B1p_rank"]), "true": int(ranks.loc[n, "true_rank"])}
                 for n, r in top.iterrows()]

    return {
        "ceiling": metrics["tau_ceiling"],
        "pairs": metrics["n_pairs"],
        "tied_pairs": metrics["pairs_tied_in_truth"],
        "zero_medal": metrics["zero_medal_nations"],
        "n_boot": metrics["n_boot"],
        "scores": [{
            "id": r.forecast, "label": r.label, "tau": float(r.tau), "lo": float(r.ci95_low), "hi": float(r.ci95_high),
            "share": float(r.share_of_ceiling), "conc": int(r.concordant), "disc": int(r.discordant),
        } for r in scores.itertuples()],
        "diffs": [{"cmp": r.comparison, "d": float(r.difference), "lo": float(r.ci95_low), "hi": float(r.ci95_high),
                   "verdict": r.verdict} for r in diffs.itertuples()],
        "nations": nations,
        "tiers": tier_rows,
        "history": hist_rows,
        "programme": prog_rows,
        "programme_total_2022": int(prog["golds_2022_all_sports"].sum()),
        "programme_dropped": int(prog["golds_2022_dropped_sports"].sum()),
        "repo": REPO_URL,
    }


def write_dashboard(root: Path, metrics: dict, out_dir: Path) -> Path:
    payload = build_payload(metrics, out_dir)
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, separators=(",", ":")).replace("</", "<\\/"))
    dest = Path(root) / "docs" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html)
    (dest.parent / ".nojekyll").write_text("")
    return dest


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Glasgow 2026 Predictability</title>
<meta name="description" content="How predictable was the Glasgow 2026 Commonwealth Games medal table? Leakage-free baselines scored with the RSS competition's Kendall's tau.">
<style>
:root{
  color-scheme: light;
  --surface-0:#f4f3f0; --surface-1:#fcfcfb; --border:#e4e3df; --grid:#ecebe7;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#7a7975;
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a; --neutral:#9a9893;
  --accent-soft:#e8f0fb;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --surface-0:#121211; --surface-1:#1a1a19; --border:#2e2e2b; --grid:#262624;
    --text-primary:#f0efec; --text-secondary:#c3c2b7; --text-muted:#8f8e86;
    --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70; --neutral:#6b6a65;
    --accent-soft:#1d2a3b;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --surface-0:#121211; --surface-1:#1a1a19; --border:#2e2e2b; --grid:#262624;
  --text-primary:#f0efec; --text-secondary:#c3c2b7; --text-muted:#8f8e86;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70; --neutral:#6b6a65;
  --accent-soft:#1d2a3b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--surface-0);color:var(--text-primary);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 48px}
header h1{font-size:26px;line-height:1.2;margin:0 0 6px;letter-spacing:-0.01em}
header p{margin:0;color:var(--text-secondary);max-width:760px}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:22px 0}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.tile .k{font-size:12px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:28px;font-weight:650;margin-top:2px;font-variant-numeric:tabular-nums}
.tile .s{font-size:13px;color:var(--text-muted)}
.panel{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:18px 18px 14px;margin-top:16px}
.panel h2{font-size:17px;margin:0 0 2px}
.panel .lede{margin:0 0 12px;color:var(--text-secondary);font-size:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid2 .panel{margin-top:16px}
svg{display:block;max-width:100%;height:auto;overflow:visible}
svg text{fill:var(--text-secondary);font-size:12px}
svg .ink{fill:var(--text-primary)}
.axis line,.axis path{stroke:var(--border)}
.gridline{stroke:var(--grid)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.seg button{background:transparent;color:var(--text-secondary);border:0;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--accent-soft);color:var(--text-primary);font-weight:600}
.seg button:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid var(--series-1);outline-offset:2px}
input[type=search]{background:var(--surface-0);color:var(--text-primary);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font:inherit;font-size:13px;min-width:200px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--text-secondary);margin:4px 0 6px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.tip{position:fixed;pointer-events:none;z-index:10;background:var(--surface-1);color:var(--text-primary);
  border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:13px;line-height:1.4;
  box-shadow:0 4px 18px rgba(0,0,0,.14);max-width:260px;opacity:0;transition:opacity .08s}
.tip b{font-weight:650}
.tip .m{color:var(--text-secondary)}
table{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;border-bottom:1px solid var(--border);text-align:right}
th:first-child,td:first-child{text-align:left}
th{color:var(--text-secondary);font-weight:600;cursor:pointer;user-select:none;white-space:nowrap}
details summary{cursor:pointer;color:var(--text-secondary);font-size:14px;margin-top:8px}
.tablewrap{max-height:360px;overflow:auto;margin-top:8px}
.verdicts{display:grid;gap:6px;margin-top:10px;font-size:14px}
.verdicts div{color:var(--text-secondary)}
.verdicts b{color:var(--text-primary)}
ul.method{margin:6px 0 0;padding-left:18px;color:var(--text-secondary);font-size:14px}
ul.method li{margin:4px 0}
a{color:var(--series-1)}
footer{margin-top:20px;color:var(--text-muted);font-size:13px}
.note{font-size:12.5px;color:var(--text-muted);margin-top:6px}
@media (max-width:820px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>How predictable was the Glasgow 2026 medal table?</h1>
  <p>Naive forecasts built only from information public before the deadline of 22 July 2026, scored with the Royal Statistical Society competition's exact Kendall's tau. All 74 nations are ranked, and nations level on gold, silver and bronze stay tied.</p>
</header>

<section class="tiles" id="tiles" aria-label="Headline numbers"></section>

<section class="panel" aria-labelledby="h-score">
  <h2 id="h-score">Scoreboard</h2>
  <p class="lede">Each forecast's score with a 95% paired nation-bootstrap interval. The dashed line is the best score any forecast could get this year.</p>
  <div id="scoreboard"></div>
  <div class="verdicts" id="verdicts"></div>
</section>

<section class="panel" aria-labelledby="h-nat">
  <h2 id="h-nat">Nation explorer</h2>
  <p class="lede">Forecast rank against final rank. Points on the diagonal were placed exactly. Hover over a point for details; the 29 nations with no medal share final rank 46.</p>
  <div class="controls">
    <div class="seg" role="group" aria-label="Forecast" id="natSeg"></div>
    <input type="search" id="natSearch" placeholder="Find a nation…" aria-label="Find a nation" list="natList">
    <datalist id="natList"></datalist>
  </div>
  <div id="scatter"></div>
  <details>
    <summary>Show all 74 nations as a table</summary>
    <div class="tablewrap"><table id="natTable"></table></div>
  </details>
</section>

<div class="grid2">
  <section class="panel" aria-labelledby="h-tier">
    <h2 id="h-tier">Where the score was lost</h2>
    <p class="lede">Score lost against the best possible, by tiers built from the 2022 table only. T1 = 2022 top 10, T2 = other 2022 medallists, T3 = no 2022 medal.</p>
    <div class="legend" id="tierLegend"></div>
    <div id="tiers"></div>
  </section>
  <section class="panel" aria-labelledby="h-hist">
    <h2 id="h-hist">Was 2026 unusually hard?</h2>
    <p class="lede">"Last Games carried forward" scored in three cycles, using only earlier tables. Bars show tau; ticks show the best possible score.</p>
    <div id="history"></div>
  </section>
</div>

<section class="panel" aria-labelledby="h-prog">
  <h2 id="h-prog">The reduced programme</h2>
  <p class="lede" id="progLede"></p>
  <div class="legend">
    <span><i style="background:var(--neutral)"></i>2022 golds, all sports</span>
    <span><i style="background:var(--series-1)"></i>2022 golds, sports kept for 2026</span>
    <span><i style="background:var(--series-2)"></i>2026 golds (actual)</span>
  </div>
  <div id="programme"></div>
</section>

<section class="panel" aria-labelledby="h-method">
  <h2 id="h-method">Method and leakage controls</h2>
  <ul class="method" id="method"></ul>
</section>

<footer id="footer"></footer>
</div>
<div class="tip" id="tip" role="tooltip"></div>

<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
const NS = 'http://www.w3.org/2000/svg';
const NAMES = {B0:'B0 all tied', B1:'B1 2022 carried forward', B1p:'B1p 2022, 2026 sports only', B2:'B2 population + GDP'};
const SHORT = {B1:'B1', B1p:'B1p', B2:'B2'};
const COLORS = {B1:'var(--series-1)', B1p:'var(--series-2)', B2:'var(--series-3)'};
const f3 = x => (x<0?'−':'') + Math.abs(x).toFixed(3);
const pct = x => Math.round(x*100) + '%';
const byId = id => document.getElementById(id);
const S = Object.fromEntries(D.scores.map(s => [s.id, s]));

function el(tag, attrs, parent){
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function txt(parent, x, y, s, attrs){
  const t = el('text', Object.assign({x, y}, attrs||{}), parent); t.textContent = s; return t;
}
const tip = byId('tip');
function showTip(html, ev){
  tip.innerHTML = html; tip.style.opacity = 1;
  const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
  let x = ev.clientX + pad, y = ev.clientY + pad;
  if (x + w > innerWidth - 8) x = ev.clientX - w - pad;
  if (y + h > innerHeight - 8) y = ev.clientY - h - pad;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function hideTip(){ tip.style.opacity = 0; }
function hover(node, html){
  node.addEventListener('mousemove', ev => showTip(html(), ev));
  node.addEventListener('mouseleave', hideTip);
}

/* ---------- tiles ---------- */
const tiles = [
  ['Best possible', f3(D.ceiling), D.tied_pairs + ' of ' + D.pairs.toLocaleString() + ' pairs tied'],
  ['B1 2022 carried forward', f3(S.B1.tau), pct(S.B1.share) + ' of best possible'],
  ['B2 population + GDP', f3(S.B2.tau), pct(S.B2.share) + ' of best possible'],
  ['Nations without a medal', String(D.zero_medal), 'all tied at the bottom'],
];
byId('tiles').innerHTML = tiles.map(t =>
  `<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join('');

/* ---------- scoreboard ---------- */
function drawScore(){
  const host = byId('scoreboard'); host.innerHTML = '';
  const narrow = host.clientWidth < 600;
  const rows = D.scores.filter(s => s.id !== 'B0');
  const W = Math.max(320, host.clientWidth), rowH = 50, top = 30, left = narrow ? 44 : 230, right = 56, H = top + rows.length*rowH + 40;
  const svg = el('svg', {viewBox:`0 0 ${W} ${H}`, width:W, height:H, role:'img', 'aria-label':'Scores with intervals'}, host);
  const x = v => left + (v + 0.05) / 1.05 * (W - left - right);
  (narrow ? [0, 0.5, 1.0] : [0, 0.2, 0.4, 0.6, 0.8, 1.0]).forEach(v => {
    el('line', {x1:x(v), x2:x(v), y1:top-10, y2:H-34, class:'gridline'}, svg);
    txt(svg, x(v), H-14, v.toFixed(1), {'text-anchor':'middle'});
  });
  el('line', {x1:x(D.ceiling), x2:x(D.ceiling), y1:top-14, y2:H-34, stroke:'var(--text-secondary)', 'stroke-dasharray':'5 4', 'stroke-width':1.5}, svg);
  txt(svg, x(D.ceiling)-6, top-16, 'best possible ' + f3(D.ceiling), {'text-anchor':'end', 'font-size':12});
  rows.forEach((s, i) => {
    const y = top + i*rowH + rowH/2;
    txt(svg, left-10, y+4, narrow ? SHORT[s.id] : NAMES[s.id], {'text-anchor':'end', class:'ink', 'font-size':13.5});
    el('line', {x1:x(s.lo), x2:x(s.hi), y1:y, y2:y, stroke:'var(--series-1)', 'stroke-width':3, 'stroke-linecap':'round'}, svg);
    el('circle', {cx:x(s.tau), cy:y, r:7, fill:'var(--series-1)', stroke:'var(--surface-1)', 'stroke-width':2}, svg);
    if (narrow) txt(svg, x(s.tau), y-12, f3(s.tau), {class:'ink', 'font-size':12.5, 'text-anchor':'middle'});
    else txt(svg, x(s.hi)+10, y+4, f3(s.tau), {class:'ink', 'font-size':13});
    const hit = el('rect', {x:left, y:y-rowH/2, width:W-left-right, height:rowH, fill:'transparent'}, svg);
    hover(hit, () => `<b>${NAMES[s.id]}</b><br>tau ${f3(s.tau)} <span class="m">[${f3(s.lo)}, ${f3(s.hi)}]</span>`+
      `<br>${pct(s.share)} of the best possible<br><span class="m">${s.conc} pairs right, ${s.disc} wrong</span>`);
  });
}
(function(){
  byId('verdicts').innerHTML = D.diffs.map(d =>
    `<div><b>${d.cmp.replace(' - ', ' vs ')}:</b> difference ${f3(d.d)}, 95% paired interval [${f3(d.lo)}, ${f3(d.hi)}] &rarr; <b>${d.verdict}</b></div>`).join('') +
    `<div class="note">A forecast "beats" another only if the paired interval excludes zero. Intervals come from ${D.n_boot.toLocaleString()} bootstrap resamples of nations; they do not capture the luck of individual finals.</div>`;
})();

/* ---------- nation explorer ---------- */
(function(){
  let current = 'B1', query = '';
  const seg = byId('natSeg');
  ['B1','B1p','B2'].forEach(f => {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = NAMES[f]; b.setAttribute('aria-pressed', f === current);
    b.onclick = () => { current = f; [...seg.children].forEach(c => c.setAttribute('aria-pressed', c === b)); draw(); table(); };
    seg.appendChild(b);
  });
  byId('natList').innerHTML = D.nations.map(n => `<option value="${n.nation}">`).join('');
  byId('natSearch').addEventListener('input', e => { query = e.target.value.trim().toLowerCase(); draw(); });

  const host = byId('scatter');
  function draw(){
    host.innerHTML = '';
    const W = Math.max(320, host.clientWidth), H = Math.round(Math.min(520, Math.max(320, W*0.6))), m = {l:52, r:16, t:16, b:52};
    const svg = el('svg', {viewBox:`0 0 ${W} ${H}`, width:W, height:H, role:'img', 'aria-label':'Forecast rank versus final rank'}, host);
    const maxR = 76;
    const x = r => m.l + (r - 0.5) / maxR * (W - m.l - m.r);
    const y = r => m.t + (r - 0.5) / 50 * (H - m.t - m.b);
    (W < 600 ? [1, 20, 40, 60] : [1, 10, 20, 30, 40, 50, 60, 70]).forEach(v => {
      el('line', {x1:x(v), x2:x(v), y1:m.t, y2:H-m.b, class:'gridline'}, svg);
      txt(svg, x(v), H-m.b+18, v, {'text-anchor':'middle'});
    });
    [1, 10, 20, 30, 40, 46].forEach(v => {
      el('line', {x1:m.l, x2:W-m.r, y1:y(v), y2:y(v), class:'gridline'}, svg);
      txt(svg, m.l-10, y(v)+4, v, {'text-anchor':'end'});
    });
    el('line', {x1:x(1), y1:y(1), x2:x(50), y2:y(50), stroke:'var(--neutral)', 'stroke-width':1.5}, svg);
    txt(svg, (m.l+W-m.r)/2, H-8, 'Forecast rank (1 = top)', {'text-anchor':'middle'});
    txt(svg, 16, (m.t+H-m.b)/2, 'Final rank', {'text-anchor':'middle', transform:`rotate(-90 16 ${(m.t+H-m.b)/2})`});
    const pts = D.nations.slice().sort((a,b) => (b[current+'_d']) - (a[current+'_d']));
    pts.forEach(n => {
      const hit = query && n.nation.toLowerCase().includes(query);
      const dim = query && !hit;
      const g = el('g', {}, svg);
      el('circle', {cx:x(n[current]), cy:y(n.true), r: hit ? 8 : 5.5,
        fill: hit ? 'var(--series-2)' : 'var(--series-1)', 'fill-opacity': dim ? 0.18 : 0.9,
        stroke:'var(--surface-1)', 'stroke-width':1.5}, g);
      if (hit) txt(g, x(n[current])+11, y(n.true)+4, n.nation, {class:'ink', 'font-size':13});
      const target = el('circle', {cx:x(n[current]), cy:y(n.true), r:11, fill:'transparent'}, g);
      hover(target, () => `<b>${n.nation}</b> <span class="m">(tier T${n.tier})</span><br>`+
        `Medals: ${n.gold} G, ${n.silver} S, ${n.bronze} B<br>Final rank ${n.true}, forecast rank ${n[current]}<br>`+
        `<span class="m">${n[current+'_c']} pairs right, ${n[current+'_d']} wrong (of 73)</span>`);
    });
  }
  function table(){
    const cols = [['nation','Nation'],['true','Final rank'],[current,'Forecast rank'],['gold','G'],['silver','S'],['bronze','B'],[current+'_c','Pairs right'],[current+'_d','Pairs wrong']];
    let sortKey = 'true', asc = true;
    const t = byId('natTable');
    function render(){
      const rows = D.nations.slice().sort((a,b) => {
        const va = a[sortKey], vb = b[sortKey];
        return (typeof va === 'string' ? va.localeCompare(vb) : va - vb) * (asc ? 1 : -1);
      });
      t.innerHTML = '<thead><tr>' + cols.map(c => `<th scope="col" data-k="${c[0]}">${c[1]}${c[0]===sortKey ? (asc?' ▲':' ▼') : ''}</th>`).join('') + '</tr></thead>' +
        '<tbody>' + rows.map(r => '<tr>' + cols.map(c => `<td>${r[c[0]]}</td>`).join('') + '</tr>').join('') + '</tbody>';
      t.querySelectorAll('th').forEach(th => th.onclick = () => {
        const k = th.dataset.k; asc = (k === sortKey) ? !asc : true; sortKey = k; render();
      });
    }
    render();
  }
  draw(); table();
  window.__redrawScatter = draw;
})();

/* ---------- tiers ---------- */
byId('tierLegend').innerHTML = ['B1','B1p','B2'].map(f => `<span><i style="background:${COLORS[f]}"></i>${NAMES[f]}</span>`).join('');
function drawTiers(){
  const fs = ['B1','B1p','B2'];
  const host = byId('tiers'); host.innerHTML = '';
  const types = D.tiers.B1.map(r => r.pair_type.replace('T1 top-10 in 2022','T1').replace('T2 other 2022 medallists','T2').replace('T3 no 2022 medal','T3'));
  const W = Math.max(300, host.clientWidth), groupH = 46, top = 6, left = 86, right = 24, H = top + types.length*groupH + 30;
  const svg = el('svg', {viewBox:`0 0 ${W} ${H}`, width:W, height:H, role:'img', 'aria-label':'Score lost by tier'}, host);
  const maxV = Math.max(...fs.flatMap(f => D.tiers[f].map(r => r.lost)));
  const x = v => left + v / (maxV*1.08) * (W - left - right);
  [0, 0.05, 0.10, 0.15].filter(v => v <= maxV*1.08).forEach(v => {
    el('line', {x1:x(v), x2:x(v), y1:top, y2:H-26, class:'gridline'}, svg);
    txt(svg, x(v), H-10, v.toFixed(2), {'text-anchor':'middle', 'font-size':11});
  });
  types.forEach((t, i) => {
    const y0 = top + i*groupH;
    txt(svg, left-8, y0 + groupH/2 + 4, t, {'text-anchor':'end', class:'ink', 'font-size':12.5});
    fs.forEach((f, j) => {
      const r = D.tiers[f][i], bh = 11, y = y0 + 6 + j*(bh+2);
      const w = Math.max(x(r.lost) - left, 1.5);
      el('rect', {x:left, y, width:w, height:bh, rx:3, fill:COLORS[f]}, svg);
      const hit = el('rect', {x:left, y:y-1, width:W-left-right, height:bh+2, fill:'transparent'}, svg);
      hover(hit, () => `<b>${t}</b> &middot; ${NAMES[f]}<br>${r.pairs} pairs, ${pct(r.tied)} tied in final table<br>`+
        `tau within ${f3(r.tau_within)}<br>score lost ${r.lost.toFixed(3)}`);
    });
  });
}

/* ---------- history ---------- */
function drawHistory(){
  const host = byId('history'); host.innerHTML = '';
  const W = Math.max(300, host.clientWidth), H = 290, m = {l:40, r:12, t:16, b:40};
  const svg = el('svg', {viewBox:`0 0 ${W} ${H}`, width:W, height:H, role:'img', 'aria-label':'Carry-forward score by cycle'}, host);
  const n = D.history.length, slot = (W - m.l - m.r) / n;
  const y = v => m.t + (1 - v) * (H - m.t - m.b);
  [0, 0.2, 0.4, 0.6, 0.8, 1.0].forEach(v => {
    el('line', {x1:m.l, x2:W-m.r, y1:y(v), y2:y(v), class:'gridline'}, svg);
    txt(svg, m.l-8, y(v)+4, v.toFixed(1), {'text-anchor':'end', 'font-size':11});
  });
  D.history.forEach((h, i) => {
    const cx = m.l + slot*i + slot/2, bw = slot*0.46;
    el('rect', {x:cx-bw/2, y:y(h.tau), width:bw, height:y(0)-y(h.tau), rx:4, fill:'var(--series-1)'}, svg);
    el('line', {x1:cx-bw/2-6, x2:cx+bw/2+6, y1:y(h.ceiling), y2:y(h.ceiling), stroke:'var(--text-primary)', 'stroke-width':2.5}, svg);
    txt(svg, cx, y(h.tau)-8, f3(h.tau), {'text-anchor':'middle', class:'ink', 'font-size':12.5});
    txt(svg, cx, H-14, (h.target-4) + ' → ' + h.target, {'text-anchor':'middle', 'font-size':12});
    const hit = el('rect', {x:cx-slot/2, y:m.t, width:slot, height:H-m.t-m.b, fill:'transparent'}, svg);
    hover(hit, () => `<b>${h.target-4} table &rarr; ${h.target}</b><br>tau ${f3(h.tau)}<br>best possible ${f3(h.ceiling)}<br>${(100*h.tau/h.ceiling).toFixed(1)}% of best possible`);
  });
}

/* ---------- programme ---------- */
byId('progLede').textContent = `Of the ${D.programme_total_2022} golds won in 2022, ${D.programme_dropped} came in sports not held in 2026. ` +
    `Counting only the kept sports (B1p) did not beat the full 2022 table (B1). It fixed some nations and broke others.`;
function drawProgramme(){
  const host = byId('programme'); host.innerHTML = '';
  const rows = D.programme, W = Math.max(320, host.clientWidth), rowH = 30, left = 104, right = 16, top = 10, H = top + rows.length*rowH + 34;
  const svg = el('svg', {viewBox:`0 0 ${W} ${H}`, width:W, height:H, role:'img', 'aria-label':'2022 golds in kept and dropped sports'}, host);
  const sx = v => v <= 5 ? v/5*0.25 : 0.25 + Math.log(v/5)/Math.log(80/5)*0.75;
  const x = v => left + sx(v) * (W - left - right);
  [0, 2, 5, 10, 20, 40, 70].forEach(v => {
    el('line', {x1:x(v), x2:x(v), y1:top, y2:H-30, class:'gridline'}, svg);
    txt(svg, x(v), H-12, v, {'text-anchor':'middle', 'font-size':11});
  });
  rows.forEach((r, i) => {
    const y = top + i*rowH + rowH/2;
    txt(svg, left-10, y+4, r.nation, {'text-anchor':'end', class:'ink', 'font-size':13});
    el('line', {x1:x(r.kept), x2:x(r.all), y1:y, y2:y, stroke:'var(--border)', 'stroke-width':4, 'stroke-linecap':'round'}, svg);
    el('circle', {cx:x(r.all), cy:y, r:6.5, fill:'var(--neutral)'}, svg);
    el('circle', {cx:x(r.kept), cy:y, r:6.5, fill:'var(--series-1)', stroke:'var(--surface-1)', 'stroke-width':1.5}, svg);
    el('rect', {x:x(r.actual)-5, y:y-5, width:10, height:10, transform:`rotate(45 ${x(r.actual)} ${y})`, fill:'var(--series-2)', stroke:'var(--surface-1)', 'stroke-width':1.5}, svg);
    const hit = el('rect', {x:0, y:y-rowH/2, width:W, height:rowH, fill:'transparent'}, svg);
    hover(hit, () => `<b>${r.nation}</b><br>2022 golds: ${r.all} (${r.kept} in sports kept for 2026)<br>2026 golds: ${r.actual}<br>`+
      `<span class="m">Rank: B1 ${r.b1}, B1p ${r.b1p}, final ${r.true}</span>`);
  });
}
function drawAll(){ drawScore(); window.__redrawScatter(); drawTiers(); drawHistory(); drawProgramme(); }
drawAll();
let lastW = innerWidth, timer = null;
addEventListener('resize', () => { if (innerWidth === lastW) return; lastW = innerWidth; clearTimeout(timer); timer = setTimeout(drawAll, 120); });

/* ---------- method ---------- */
const R = D.repo + '/blob/main/';
byId('method').innerHTML = [
  `<b>Two-stage code.</b> Forecasts are built from data that never contains the 2026 results; a test rebuilds them with the results file deleted and checks they are identical.`,
  `<b>Point-in-time features.</b> Population and GDP come from CIA World Factbook snapshots pinned by git commit. The 2026 snapshot is dated 17 May 2026, before the deadline.`,
  `<b>No tuning on 2026.</b> The baselines have no free parameters; the population + GDP model is trained on 2018 and 2022 only.`,
  `<b>The competition's exact metric.</b> Tied pairs score zero and stay in the denominator, so the best possible score is ${f3(D.ceiling)}, not 1.`,
  `<b>Plan committed before scoring.</b> Later changes are logged with their reasons; none changes a score or verdict.`,
  `Details: <a href="${R}LEAKAGE_AUDIT.md">leakage audit</a> &middot; <a href="${R}ANALYSIS_PLAN.md">analysis plan</a> &middot; <a href="${R}REPORT.md">full report</a> &middot; <a href="${R}DATA_SOURCES.md">data sources</a>`
].map(s => `<li>${s}</li>`).join('');
byId('footer').innerHTML = `Built by Ridhima Gupta &middot; <a href="${D.repo}">Source code and data on GitHub</a> &middot; every number on this page is generated from the repository's results by code.`;
})();
</script>
</body>
</html>
"""
