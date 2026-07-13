# 🚴 Tour de France Kicktipp

A web-based betting game for the **Tour de France** — play against your friends by predicting stage winners, the yellow jersey, and more. Inspired by [Kicktipp](https://www.kicktipp.de/), reimagined for cycling's greatest race.

> ⚠️ **Early stage** — this repo is a work in progress. Sections marked _TBD_ will be filled in as the stack and features are decided.

## 🎯 What is this?

Every year the Tour de France runs 21 stages over three weeks. This app lets a group of friends compete in a season-long prediction game:

- Predict the outcome of each stage (and the overall race).
- Earn points based on how accurate your tips are.
- Watch the standings shift day by day on a shared leaderboard.

Think of it as a fantasy league / betting pool for cycling fans — no real money, just bragging rights.

## ✨ Features

- **Tip submission** — place your predictions before each stage locks.
- **Automatic scoring** — points awarded once official results are in.
- **Leaderboard** — live overall and per-stage rankings among your group.
- **Private leagues** — create a group and invite friends to compete.
- **Stage calendar** — see upcoming stages, deadlines, and results.

_(Feature list is aspirational and will be trimmed/expanded as the app is built.)_

## 🏆 How scoring works

Points are awarded per prediction. A typical scheme:

| Prediction            | Points |
| --------------------- | ------ |
| Correct stage winner  | _TBD_  |
| Podium (top 3)        | _TBD_  |
| Yellow jersey (GC)    | _TBD_  |
| Points/KOM classification | _TBD_ |

The final scoring rules are still being defined — see [Roadmap](#-roadmap).

## 🛠️ Tech stack

_TBD._ The stack hasn't been finalized yet. Candidate pieces:

- **Frontend:** _TBD_
- **Backend / API:** _TBD_
- **Database:** _TBD_
- **Results data source:** an official/third-party Tour de France results feed, or manual entry.

## 🚀 Getting started

> These are placeholder instructions — update them once the stack is chosen.

### Prerequisites

- _TBD (e.g. Node.js / Python / a database)_

### Setup

```bash
# Clone the repo
git clone https://github.com/chrisdiss/tourdefrance-kicktipp.git
cd tourdefrance-kicktipp

# Install dependencies
# TBD

# Configure environment variables (see below)
cp .env.example .env

# Run the app locally
# TBD
```

### Environment variables

| Variable | Description        |
| -------- | ------------------ |
| _TBD_    | _TBD_              |

## 📁 Project structure

```
tourdefrance-kicktipp/
├── README.md
└── ...   # TBD
```

## 🗺️ Roadmap

- [ ] Decide on the tech stack
- [ ] User accounts & authentication
- [ ] Create/join private leagues
- [ ] Stage calendar with tipping deadlines
- [ ] Tip submission form
- [ ] Automatic result import & scoring
- [ ] Live leaderboard
- [ ] Notifications / reminders before deadlines

## 🤝 Contributing

Contributions and ideas are welcome! Open an issue to discuss a feature or bug before submitting a pull request.

## 📄 License

_TBD — add a license (e.g. MIT) before publishing._

---

_Not affiliated with Kicktipp or the Tour de France / A.S.O. This is a hobby project for friends._
