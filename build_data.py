#!/usr/bin/env python3
"""
build_data.py — erzeugt data.js aus dem Master-Dokument tdf_tippspiel_master.xlsx.

Die xlsx ist die einzige Datenquelle ("single source of truth"). Nach jeder
Aktualisierung (neue Etappe eingetragen, Ergebnis korrigiert, Spruch geändert …)
einfach dieses Skript ausführen:

    python build_data.py

index.html / support.js bleiben unverändert — die Export-Struktur von data.js
ist identisch zu vorher, nur dass die Etappenwerte jetzt echt (aus den
Ergebnissen berechnet) statt geschätzt sind.

Wie die Punkte entstehen (identisch zur Excel-Logik, hier in Python nachgebaut,
damit das Ergebnis NICHT davon abhängt, ob Excel die Formeln neu berechnet hat):

  Punkte eines Fahrers/Teams je Etappe
      = Summe der Punktematrix-Werte für jede Platzierung/Wertung,
        in der er/sie in dieser Etappe in 'Ergebnisse_Roh' steht.
  Punkte eines Spielers je Etappe
      = Summe der Punkte all seiner getippten Fahrer + seines Team-Tipps.

Roh-Eingaben, die gepflegt werden (alles andere wird berechnet):
  - "Ergebnisse_Roh"  Platzierungen 1–15 + Trikots + Mannschaft je Etappe
  - "Punktematrix"     Punkte je Platzierung / Wertung
  - "Spieler_Teams"    Spalte A/B: welcher Spieler tippt welche Fahrer + 1 Team
  - "Startlist2026"    Fahrer-Stammdaten (BIB, Specialty, Age, Rider, Team)
  - "Quotes"           Teamfunk / Trash-Talk (Spalten: Spieler, Spruch)
"""

import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl fehlt — bitte 'pip install openpyxl' ausführen.")

ROOT = Path(__file__).resolve().parent
XLSX = ROOT / "tdf_tippspiel_master.xlsx"
OUT = ROOT / "data.js"

# Gesamtzahl Etappen der Tour. Wie viele bereits gefahren sind, ergibt sich
# automatisch aus den befüllten Etappen-Spalten in 'Ergebnisse_Roh'.
STAGES_TOTAL = 21


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------
_REF_RE = re.compile(r"^=\s*(?:'([^']+)'|([A-Za-z0-9_]+))?!?\$?([A-Z]+)\$?(\d+)\s*$")


def resolve(wb, value, depth=0):
    """Löst einfache Zellformeln wie =Startlist2026!D2 oder =A1 zum Wert auf.
    Nötig, weil einige Tipp-Zellen als Verweise statt als Text gespeichert sind
    (und deren Cache-Wert beim Bearbeiten verloren gehen kann). Komplexe
    Formeln -> None."""
    if not isinstance(value, str) or not value.startswith("="):
        return value
    if depth > 5:
        return None
    m = _REF_RE.match(value)
    if not m:
        return None
    sheet = m.group(1) or m.group(2)
    ref = f"{m.group(3)}{m.group(4)}"
    try:
        ws = wb[sheet] if sheet else None
    except KeyError:
        return None
    if ws is None:
        return None
    return resolve(wb, ws[ref].value, depth + 1)


def split_rider_name(core):
    """'PogačarTadej' -> 'Pogačar Tadej'. Leerzeichen an der letzten
    Kleinbuchstabe→Großbuchstabe-Grenze (Nachname/Vorname)."""
    boundary = -1
    for i in range(1, len(core)):
        if core[i - 1].islower() and core[i].isupper():
            boundary = i
    return core if boundary < 1 else core[:boundary] + " " + core[boundary:]


def js_str(s):
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"


def stage_columns(ws, header_row=1):
    """Spaltenindizes der Etappen-Spalten (S01, 'S 01', Stage01 …)."""
    cols = []
    for c in range(1, ws.max_column + 1):
        v = ws.cell(header_row, c).value
        if isinstance(v, str) and re.match(r"^\s*(S|Stage)\s*0*\d+\s*$", v):
            cols.append(c)
    return cols


# --------------------------------------------------------------------------
# Einlesen der Roh-Eingaben
# --------------------------------------------------------------------------
def read_points_matrix(wb):
    ws = wb["Punktematrix"]
    pts = {}
    for r in range(2, ws.max_row + 1):
        label, p = ws.cell(r, 1).value, ws.cell(r, 2).value
        if label is not None and p is not None:
            pts[str(label).strip()] = int(p)
    return pts


def read_entity_stage_points(wb, pts_map):
    """Punkte je Fahrer/Team und Etappe aus 'Ergebnisse_Roh'.
    Rückgabe: (dict entity -> [pkt je etappe], stages_done)."""
    ws = wb["Ergebnisse_Roh"]
    scols = stage_columns(ws)
    n = len(scols)
    ent = defaultdict(lambda: [0] * n)
    stage_has_data = [False] * n
    for r in range(2, ws.max_row + 1):
        label = ws.cell(r, 2).value          # Platz / Trikot / Mannschaft
        if label is None:
            continue
        p = pts_map.get(str(label).strip())
        if p is None:
            continue
        for si, c in enumerate(scols):
            who = ws.cell(r, c).value
            if who not in (None, ""):
                ent[who][si] += p
                stage_has_data[si] = True
    stages_done = sum(1 for x in stage_has_data if x)
    return ent, stages_done


def read_tips(wb, teams):
    """Spalte A/B aus 'Spieler_Teams': Fahrer-Tipps + Team-Tipp je Spieler.
    Spalte B kann Verweise (=Startlist2026!Dxx) enthalten -> auflösen."""
    ws = wb["Spieler_Teams"]
    rider_picks = defaultdict(list)   # spieler -> [rider_key]
    team_pick = {}                    # spieler -> teamname
    tipped_by = defaultdict(set)      # rider_key -> {spieler}
    for r in range(2, ws.max_row + 1):
        sp = resolve(wb, ws.cell(r, 1).value)
        fa = resolve(wb, ws.cell(r, 2).value)
        if not sp or not fa:
            continue
        if fa in teams:
            team_pick[sp] = fa
        else:
            rider_picks[sp].append(fa)
            tipped_by[fa].add(sp)
    return rider_picks, team_pick, tipped_by


def read_startlist(wb):
    """Fahrer-Stammdaten (ohne Punkte — die werden berechnet)."""
    ws = wb["Startlist2026"]
    riders = {}
    teams = set()
    for r in range(2, ws.max_row + 1):
        bib = ws.cell(r, 1).value
        spec = ws.cell(r, 2).value
        age = ws.cell(r, 3).value
        key = ws.cell(r, 4).value
        team = ws.cell(r, 5).value
        if team:
            teams.add(team)
        if not key or not team or key == team:
            continue
        core = key[: -len(team)] if key.endswith(team) else key
        riders[key] = {
            "name": split_rider_name(core),
            "team": team,
            "spec": spec,
            "age": int(age) if age is not None else None,
            "bib": int(bib) if bib is not None else None,
        }
    return riders, teams


def read_quotes(wb):
    if "Quotes" not in wb.sheetnames:
        return []
    ws = wb["Quotes"]
    out = []
    for r in range(2, ws.max_row + 1):
        by, txt = ws.cell(r, 1).value, ws.cell(r, 2).value
        if by and txt:
            out.append({"by": str(by), "txt": str(txt)})
    return out


# --------------------------------------------------------------------------
# Statistik ableiten
# --------------------------------------------------------------------------
def best_worst(stages):
    best_i = max(range(len(stages)), key=lambda i: (stages[i], -i))
    worst_i = min(range(len(stages)), key=lambda i: (stages[i], i))
    return [best_i + 1, stages[best_i]], [worst_i + 1, stages[worst_i]]


def compute_ranks(player_stages, names):
    """ranks[i] = Platz in der Gesamtwertung nach Etappe i.
    Standard-Competition-Ranking: Gleichstände teilen sich den Platz
    (…8, 8, 10…), wie in der ursprünglichen Kicktipp-Wertung."""
    n = len(next(iter(player_stages.values())))
    cum = {name: 0 for name in names}
    ranks = {name: [] for name in names}
    for i in range(n):
        for name in names:
            cum[name] += player_stages[name][i]
        for name in names:
            better = sum(1 for o in names if cum[o] > cum[name])
            ranks[name].append(better + 1)
    return ranks


# --------------------------------------------------------------------------
# Aufbau + Ausgabe
# --------------------------------------------------------------------------
def build():
    if not XLSX.exists():
        sys.exit(f"Master-Datei nicht gefunden: {XLSX}")
    # data_only=False: Literale kommen direkt, Formel-Verweise als Text
    # (werden via resolve() aufgelöst) — unabhängig von Excel-Cache-Werten.
    wb = openpyxl.load_workbook(XLSX, data_only=False)

    pts_map = read_points_matrix(wb)
    ent, stages_done = read_entity_stage_points(wb, pts_map)
    riders_meta, teams = read_startlist(wb)
    rider_picks, team_pick, tipped_by = read_tips(wb, teams)
    quotes = read_quotes(wb)

    if stages_done == 0:
        sys.exit("Keine gefahrenen Etappen in 'Ergebnisse_Roh' gefunden.")

    def ent_stages(name):
        return (ent.get(name) or [0] * stages_done)[:stages_done]

    # ---- Spieler ----
    player_names = sorted(rider_picks.keys() | team_pick.keys(), key=str.casefold)
    player_stages = {}
    for name in player_names:
        st = [0] * stages_done
        for f in rider_picks.get(name, []):
            for i, v in enumerate(ent_stages(f)):
                st[i] += v
        tp = team_pick.get(name)
        if tp:
            for i, v in enumerate(ent_stages(tp)):
                st[i] += v
        player_stages[name] = st

    ranks = compute_ranks(player_stages, player_names)

    players_js = []
    for name in player_names:
        st = player_stages[name]
        total = sum(st)
        best, worst = best_worst(st)
        tp = team_pick.get(name)
        tip_pts = sum(ent_stages(tp)) if tp else 0
        players_js.append({
            "n": name,
            "avg": round(total / stages_done, 1),
            "best": best, "worst": worst,
            "tip": tp, "tipPts": tip_pts,
            "stages": st, "ranks": ranks[name],
        })

    # ---- Fahrer (nur getippte oder punktende) ----
    rel = []
    all_rider_keys = set(riders_meta) | set(tipped_by)
    for key in all_rider_keys:
        if key in teams:
            continue
        st = ent_stages(key)
        p = sum(st)
        by = sorted(tipped_by.get(key, ()), key=str.casefold)
        if p <= 0 and not by:
            continue
        meta = riders_meta.get(key)
        if meta is None:  # getippt, aber nicht in Startliste
            core = key
            meta = {"name": split_rider_name(core), "team": None,
                    "spec": None, "age": None, "bib": None}
        mx = max(st) if st else 0
        bd = [st.index(mx) + 1, mx] if mx > 0 else None
        rel.append({
            "n": meta["name"], "t": meta["team"], "s": meta["spec"],
            "a": meta["age"], "b": meta["bib"], "p": p, "bd": bd, "by": by,
        })
    rel.sort(key=lambda x: (-x["p"], x["n"].casefold()))

    # ---- Team-Tipp-Punkte (nur getippte Teams mit Punkten) ----
    team_pts = {}
    for name in player_names:
        t = team_pick.get(name)
        if t:
            pts = sum(ent_stages(t))
            if pts > 0:
                team_pts[t] = pts

    write_data_js(stages_done, players_js, rel, team_pts, quotes)

    print(f"✓ data.js geschrieben ({OUT})")
    print(f"  Etappen gefahren: {stages_done} / {STAGES_TOTAL}")
    print(f"  Spieler:          {len(players_js)}")
    print(f"  Fahrer (relevant):{len(rel)}")
    print(f"  Team-Tipps:       {len(team_pts)}")
    print(f"  Sprüche:          {len(quotes)}")


def write_data_js(stages_done, players_js, rel, team_pts, quotes):
    o = []
    o.append("// Tour de France 2026 Tipprunde — Daten")
    o.append("// ⚠️  AUTOMATISCH GENERIERT von build_data.py aus tdf_tippspiel_master.xlsx.")
    o.append("//     Nicht von Hand bearbeiten — stattdessen die xlsx ändern und")
    o.append("//     `python build_data.py` ausführen.")
    o.append(f"export const STAGES_DONE = {stages_done};")
    o.append(f"export const STAGES_TOTAL = {STAGES_TOTAL};")
    o.append("")

    o.append("export const PLAYERS = [")
    for p in players_js:
        tip = js_str(p["tip"]) if p["tip"] else "null"
        o.append(
            "  {{n:{n}, avg:{avg}, best:[{b0},{b1}], worst:[{w0},{w1}], "
            "tip:{tip}, tipPts:{tp}, stages:[{st}], ranks:[{rk}]}},".format(
                n=js_str(p["n"]), avg=p["avg"],
                b0=p["best"][0], b1=p["best"][1],
                w0=p["worst"][0], w1=p["worst"][1],
                tip=tip, tp=p["tipPts"],
                st=",".join(map(str, p["stages"])),
                rk=",".join(map(str, p["ranks"])),
            )
        )
    o.append("];")
    o.append("")

    o.append("// Fahrer: n, t=Team, s=Spezialist, a=Alter, b=Startnummer, p=Punkte gesamt,")
    o.append("// bd=[Etappe,Punkte] bester Tag, by=getippt von")
    o.append("export const RIDERS = [")
    for r in rel:
        bd = "null" if r["bd"] is None else f"[{r['bd'][0]},{r['bd'][1]}]"
        by = ",".join(js_str(x) for x in r["by"])
        t = js_str(r["t"]) if r["t"] else "null"
        s = js_str(r["s"]) if r["s"] else "null"
        a = r["a"] if r["a"] is not None else "null"
        b = r["b"] if r["b"] is not None else "null"
        o.append(
            "  {{n:{n}, t:{t}, s:{s}, a:{a}, b:{b}, p:{p}, bd:{bd}, by:[{by}]}},".format(
                n=js_str(r["n"]), t=t, s=s, a=a, b=b, p=r["p"], bd=bd, by=by,
            )
        )
    o.append("];")
    o.append("")

    o.append("// Teamwertungs-Punkte je Team (nur Teams mit Punkten)")
    o.append("export const TEAM_TIP_PTS = {")
    for t, pts in sorted(team_pts.items(), key=lambda kv: (-kv[1], kv[0])):
        o.append(f"  {js_str(t)}: {pts},")
    o.append("};")
    o.append("")

    o.append("// Teamfunk — Trash Talk der Runde (Sheet 'Quotes' in der xlsx pflegen).")
    o.append("export const QUOTES = [")
    for q in quotes:
        o.append(f"  {{by:{js_str(q['by'])}, txt:{js_str(q['txt'])}}},")
    o.append("];")
    o.append("")

    o.append("""export function buildPlayers(){
  return PLAYERS.map(p => {
    const stages = p.stages;
    const total = stages.reduce((a, b) => a + b, 0);
    const cum = []; let s = 0;
    stages.forEach(v => { s += v; cum.push(s); });
    return { ...p, total, cum };
  });
}
""")

    OUT.write_text("\n".join(o), encoding="utf-8")


if __name__ == "__main__":
    build()
