# 🏏 IPL Intelligence Platform

> AI-Driven Decision Support System for IPL Teams, Analysts & Commentators

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-orange)](https://sqlite.org)
[![PWA](https://img.shields.io/badge/PWA-Ready-purple)](https://web.dev/pwa)

---

## 📌 Overview

IPL Intelligence is a full-stack analytics and decision-support platform built for IPL teams, analysts, commentators, and content creators. It transforms raw ball-by-ball IPL data (2008–2024) into actionable insights through advanced analytics, player valuation models, and an interactive auction simulation engine.

---

## 🚀 Live Features

### 🔐 Authentication & Role-Based Access
- **Admin** — Full platform control, all team data, system management
- **Team Management** — Each IPL team has its own login (CSK, MI, RCB, KKR, DC, RR, SRH, PBKS, LSG, GT)
- **Analyst** — Read-only access to all analytics modules
- JWT-based authentication with 8-hour session tokens

### 📊 Player Analytics
- Batting leaderboard with season filters (2008–2024)
- Bowling leaderboard with economy, wickets, strike rate
- **Custom Impact Score** — weighted formula combining batting + bowling contribution
- Phase-wise analysis — Powerplay, Middle, Death overs
- Form tracker — last 15 matches trend
- Season-by-season trend charts
- Skill radar charts

### ⚔ Player Comparison
- Head-to-head comparison of any two players
- Dual radar chart overlay
- Phase-wise runs comparison
- Season trend line chart
- Winner detection per metric

### 🏟 Team Dashboard
- All 10 current IPL teams
- Historical win rates (2008–2024)
- Top batters and bowlers per team
- Season history with win/loss charts
- Head-to-head (H2H) match records

### 🔨 Auction Strategy Engine (USP)
- **2026 IPL Auction Pool** — 346 players with reserve & expected prices
- Team-wise retained squads (real 2025 IPL retention data)
- Real auction budget after retention deductions
- Live bid simulation with overpay warnings
- Squad gap detection (batters, bowlers, wicketkeepers, overseas)
- Best XI suggestion
- Overseas slot tracker (max 4)

### 📄 Export Features
- **PDF Reports** — Player profile, player comparison, squad report
- **CSV Export** — Squad list, comparison data
- Professional dark-themed PDF with tables and verdict

### 👑 Admin Dashboard
- All 10 team budget overview
- Total retention spend across league
- Full retained players table
- Platform stats (1,095 matches, 260,920 deliveries, 346 auction players)
- Team credentials management

### 📱 Progressive Web App (PWA)
- Installable on desktop and mobile
- Offline capability via service worker
- Native app experience

---

## 🗃 Dataset

- **matches.csv** — 1,095 IPL matches (2008–2024)
- **deliveries.csv** — 260,920 ball-by-ball records
- **auction_market_2026.csv** — 346 players in IPL 2026 auction pool

Data source: Kaggle IPL Complete Dataset

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy, Pandas |
| Analytics | NumPy, Custom scoring models |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Charts | Chart.js |
| Auth | JWT (python-jose), SHA256 hashing |
| PDF Export | ReportLab |
| PWA | Web Manifest, Service Worker |
| Version Control | Git, GitHub |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/abduldon/ipl-intelligence.git
cd ipl-intelligence

# 2. Create virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add dataset files to data/raw/
# - matches.csv
# - deliveries.csv
# - auction_market_2026.csv
# Download from: https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020

# 5. Run data ingestion
cd data
python ingest.py
cd ..

# 6. Start the server
python run.py
```

Open `http://localhost:8000/login` in your browser.

---

## 🔑 Login Credentials

| Role | Username | Password |
|------|----------|----------|
| 👑 Admin | `admin` | `admin123` |
| 🟡 CSK | `csk` | `csk2025` |
| 🔵 MI | `mi` | `mi2025` |
| 🔴 RCB | `rcb` | `rcb2025` |
| 🟣 KKR | `kkr` | `kkr2025` |
| 💙 DC | `dc` | `dc2025` |
| 🩵 RR | `rr` | `rr2025` |
| 🟠 SRH | `srh` | `srh2025` |
| 🔴 PBKS | `pbks` | `pbks2025` |
| 🩵 LSG | `lsg` | `lsg2025` |
| 🔵 GT | `gt` | `gt2025` |
| 📊 Analyst | `analyst` | `analyst123` |

---

## 📁 Project Structure

ipl-intelligence/
├── backend/
│   ├── analytics/
│   │   ├── player_stats.py      # Batting, bowling, impact score
│   │   ├── team_stats.py        # Team performance, H2H
│   │   ├── auction_engine.py    # Player valuation model
│   │   └── squad_data.py        # 2025 retention data
│   ├── routes/
│   │   ├── players.py           # Player API endpoints
│   │   ├── teams.py             # Team API endpoints
│   │   ├── auction.py           # Auction API endpoints
│   │   ├── export.py            # PDF/CSV export endpoints
│   │   ├── auth_routes.py       # Login/logout endpoints
│   │   └── squad_routes.py      # Squad & auction pool endpoints
│   ├── auth.py                  # JWT authentication
│   └── main.py                  # FastAPI app entry point
├── frontend/
│   ├── index.html               # Main app (PWA shell)
│   ├── login.html               # Login page
│   ├── manifest.json            # PWA manifest
│   └── sw.js                    # Service worker
├── data/
│   ├── raw/                     # CSV files go here
│   └── ingest.py                # Data pipeline script
├── run.py                       # Server startup
└── requirements.txt

---

## 🧠 Custom Analytics Models

### Impact Score Formula

Batting Score = (Total Runs / 50) + (Strike Rate / 100)
Bowling Score = (Wickets × 2) + max(0, 12 - Economy)
Impact Score  = (Batting Score × 0.6) + (Bowling Score × 0.4)

### Player Valuation Model

Base Value    = ₹0.5 Cr (minimum)
Batting Value = (Runs/1000 × 3) + (SR/200 × 2)
Bowling Value = (Wickets/50 × 3) + Economy Score
Experience    = min(2, Matches/50)
Total Value   = Base + Batting + Bowling + Experience
Min Bid       = Total × 0.6
Max Bid       = Total × 1.4

---

## <img width="1916" height="854" alt="image" src="https://github.com/user-attachments/assets/41dc5dad-4a28-4f12-8cd3-c8df8ecb48d0" />


> Login Page → Team Portal (CSK) → Admin Dashboard → Player Profile → Auction Engine

---

## 🏆 Built For

This project was built as part of a hackathon focused on **AI-Driven Workforce Development & Skill Intelligence**, adapted for IPL team management and player analytics.

---

## 👨‍💻 Developer

**Abdul Shuaib**
- GitHub: [@abduldon](https://github.com/abduldon)
- Project: IPL Intelligence Platform

---

## 📝 License

MIT License — feel free to use, modify and distribute.

---

> *"Data beats intuition. Strategy beats luck."*
