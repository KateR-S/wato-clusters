# WATO Clusters – DNA Family Tree Analysis

A full-stack web application that helps genealogists place unknown DNA relatives onto their family tree.

Upload a known family tree (GEDCOM file), define a "floating cluster" of unknown relatives whose relationships to each other you know, add centimorgans (cM) DNA match values between your tree people and cluster people, and the app will generate ranked hypotheses for exactly where those unknown relatives belong on your family tree.

Inspired by [DNA Painter WATO+](https://dnapainter.com/help/user-guide/wato-plus), with the added ability to define **multiple unknown people with known relationships to each other** and analyse the network simultaneously.

---

## Features

- **User accounts** – each user logs in and saves their own trees
- **GEDCOM import** – upload a `.ged` file to populate a family tree instantly
- **Interactive tree editor** – add/remove people and relationships (including half-relationships)
- **Floating cluster** – define a second "unknown" tree of DNA matches with known relationships between them
- **DNA cM match entry** – link each tree person to cluster people with their observed centimorgan value and approximate birth year
- **Hypothesis engine** – generates and ranks all viable placements using ISOGG cM ranges and birth-year constraints (no parent before age 14)
- **Hypothesis table** – colour-coded likelihood display (green ≥50 %, yellow 20–50 %, red < 20 %)
- **Family tree visualisation** – interactive D3 tree chart

---

## Architecture

```
wato-clusters/
├── backend/   # Python 3.12 · FastAPI · SQLAlchemy · SQLite · JWT auth
└── frontend/  # React 18 · TypeScript · Vite · TailwindCSS · react-d3-tree
```

---

## Running locally

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10 + |
| Node.js | 18 + |
| npm | 9 + |

---

### 1 · Backend

```bash
# from the repository root
cd backend

# create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# (optional) copy and edit the example environment file
cp .env.example .env
# set a secure SECRET_KEY in .env, e.g.:
#   SECRET_KEY=your-very-long-random-secret-key

# start the development server
uvicorn app.main:app --reload --port 8000
```

The API is now available at **http://localhost:8000**.  
Interactive API docs: **http://localhost:8000/docs**

#### Backend tests

```bash
cd backend
pytest -v
```

---

### 2 · Frontend

```bash
# from the repository root
cd frontend

# install dependencies
npm install

# start the development server
npm run dev
```

The app is now available at **http://localhost:5173**.

#### Frontend tests

```bash
cd frontend
npm test -- --run
```

#### Frontend production build

```bash
cd frontend
npm run build
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `changeme-secret` | JWT signing key – **change this in production** |
| `DATABASE_URL` | `sqlite:///./database.db` | SQLAlchemy database URL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 h) | JWT expiry |

Copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY` to a long random string before running in production.

---

## Usage walkthrough

1. **Register / Log in** at http://localhost:5173
2. **Dashboard** – create a new tree (or upload a GEDCOM file)
3. **Tree page** – view the D3 tree chart; add/remove people and relationships from the sidebar
4. **Create a cluster** from the Dashboard – add the unknown DNA relatives and the relationships between them
5. **Tree page → Matches** – for each tree person, record the cM value of their DNA match to each cluster person
6. **Generate Hypotheses** – click the button to see all viable placements ranked by likelihood

---

## cM ranges used (ISOGG)

| Relationship | Min cM | Max cM |
|---|---|---|
| Parent / Child | 2376 | 3720 |
| Full sibling | 1613 | 3488 |
| Grandparent / Grandchild | 984 | 2311 |
| Half sibling | 1160 | 2650 |
| Aunt/Uncle / Niece/Nephew | 1156 | 2311 |
| 1st cousin | 553 | 1225 |
| Half aunt/uncle / half niece/nephew | 500 | 1446 |
| 1st cousin once removed | 141 | 851 |
| 2nd cousin | 46 | 515 |
| 3rd cousin | 0 | 173 |

Reference: https://isogg.org/wiki/Autosomal_DNA_statistics

---

## License

MIT
