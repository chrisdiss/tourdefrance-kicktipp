# 🚴 Tour de France Kicktipp

A web-based betting/prediction game for the **Tour de France 2026** — play against your friends by tipping riders, stages, and team classifications, à la [Kicktipp](https://www.kicktipp.de/). This repo contains a working, deployable front-end that visualizes the standings of a real Tipprunde ("Osti's Freunde").

The UI was designed in [Claude Design](https://claude.ai/design) and ships as a self-contained static site — no build step required.

> **Status:** This is a **read-only standings dashboard** for an existing Tipprunde. All data is maintained in one master spreadsheet — **`tdf_tippspiel_master.xlsx`** — and compiled into `data.js` by `build_data.py` (current snapshot: after stage 9 of 21). There is no login and no online tip submission yet — those are on the roadmap below.

## 🎬 Live demo

Once GitHub Pages is enabled (see below), the app is served at:

```
https://chrisdiss.github.io/tourdefrance-kicktipp/
```

`index.html` is the **Le Tour** (light) theme. A second **Nachtfahrt** (dark) theme is available via the design switcher in the top-right of the nav.

## ✨ Features

The app currently visualizes a full season's standings across five tabs:

- **Gesamtstand** — overall leaderboard with rank deltas, jersey badges (Maillot Jaune, green/polka-dot, Lanterne Rouge, and more), rank-history sparklines, and a rotating "Teamfunk / Trash Talk" quote box.
- **Etappen** — per-stage points with a stage picker, daily winner, horizontal bar rankings, and a cumulative points line chart with a toggleable legend.
- **Fahrer** — best rider picks, searchable rider list, sort by points or by how often a rider was tipped.
- **Teams** — team-classification points aggregated per team, plus each player's team tip.
- **Duell** — head-to-head comparison of any two players (shared picks, exclusive picks, stat-by-stat).

Clicking any player or rider opens a detail drawer with stats, badges, rank history, and their picks.

## 🛠️ Tech stack

- **Vanilla static site** — plain HTML/CSS/JS, no bundler, no npm install.
- **Claude Design runtime** (`support.js`) — a small client-side runtime that renders the `<x-dc>` template (with `{{ }}` bindings, `sc-for`, `sc-if`) as a React component. It auto-loads React 18 (UMD) from a CDN at runtime.
- **Master data** (`tdf_tippspiel_master.xlsx`) — the single source of truth: stage results, points matrix, tips, startlist and quotes.
- **Build step** (`build_data.py`) — reads the xlsx, computes all points/ranks and writes `data.js`.
- **Data module** (`data.js`) — a generated ES module holding all players, riders, quotes, and their computed stats.
- **Fonts** — Archivo + Saira Condensed via Google Fonts.

> Because the page uses ES-module imports and `fetch`, it must be served over **HTTP** — opening `index.html` directly from the file system (`file://`) will not work.

## 🚀 Getting started

### Run locally

Any static file server works. For example:

```bash
git clone https://github.com/chrisdiss/tourdefrance-kicktipp.git
cd tourdefrance-kicktipp

# Python (built in on most systems)
python3 -m http.server 8000
#  → open http://localhost:8000

# …or Node
npx serve .
```

Then open the printed URL in your browser. An internet connection is required (React and the fonts load from CDNs).

### Deploy on GitHub Pages

1. Push to the `main` branch (already done).
2. In the repo, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source: Deploy from a branch**, **Branch: `main`**, folder **`/ (root)`**, and save.
4. Wait a minute, then visit `https://chrisdiss.github.io/tourdefrance-kicktipp/`.

A `.nojekyll` file is included so GitHub Pages serves every file as-is.

## 📁 Project structure

```
tourdefrance-kicktipp/
├── index.html                        # Default page — Le Tour (light) theme
├── TdF-Tipprunde-LeTour.dc.html      # Le Tour design (source)
├── TdF-Tipprunde-Nachtfahrt.dc.html  # Nachtfahrt (dark) design
├── support.js                        # Claude Design client runtime (generated — do not edit)
├── tdf_tippspiel_master.xlsx         # ⭐ Master data — the single source of truth
├── build_data.py                     # Reads the xlsx → generates data.js
├── data.js                           # Generated stats (do not edit by hand)
├── .github/workflows/build-data.yml  # CI: rebuilds data.js when the xlsx changes
├── .nojekyll                         # Serve files untouched on GitHub Pages
└── README.md
```

## 📊 Updating the data

**`tdf_tippspiel_master.xlsx` is the single source of truth.** Edit the spreadsheet, then rebuild `data.js`:

```bash
pip install openpyxl        # once
python build_data.py
```

Push the changed `tdf_tippspiel_master.xlsx` to `main` and the included **GitHub Action** rebuilds and commits `data.js` for you automatically — so in practice you just update the spreadsheet.

What lives in which sheet (only these are edited by hand; everything else is computed):

- **`Ergebnisse_Roh`** — the raw stage results: riders in places 1–15 plus the jersey and team classifications, one column per stage. Add a stage by filling a new `S…` column.
- **`Punktematrix`** — points awarded per place / classification.
- **`Spieler_Teams`** — columns A/B: which riders (and one team) each player tipped.
- **`Startlist2026`** — rider master data (bib, specialty, age, name, team).
- **`Quotes`** — the rotating "Teamfunk" trash-talk messages (columns: Spieler, Spruch).

`build_data.py` recomputes rider, player and team points exactly the way the Excel formulas do (results × points matrix), so per-stage values are **real**, not estimated. It writes `STAGES_DONE`/`STAGES_TOTAL`, `PLAYERS`, `RIDERS`, `TEAM_TIP_PTS` and `QUOTES` into `data.js`.

## 🗺️ Roadmap

- [x] Standings visualization (overall, stages, riders, teams, duel)
- [x] Two visual themes (Le Tour / Nachtfahrt)
- [ ] User accounts & authentication
- [ ] Create/join private leagues online
- [ ] Tip submission form with per-stage deadlines
- [x] Single-spreadsheet data pipeline (`tdf_tippspiel_master.xlsx` → `build_data.py` → `data.js`, auto-built in CI)
- [ ] Automatic result import from the official timing feed
- [ ] Notifications / reminders before deadlines

## 🤝 Contributing

Contributions and ideas are welcome! Open an issue to discuss a feature or bug before submitting a pull request.

## 📄 License

_TBD — add a license (e.g. MIT) before publishing more widely._

---

_Not affiliated with Kicktipp or the Tour de France / A.S.O. This is a hobby project for friends._
