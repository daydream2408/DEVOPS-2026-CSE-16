# Monte Carlo Options Pricing & Risk Simulator

Full-stack quant project: FastAPI backend runs Monte Carlo simulations for
European/Asian/Barrier options, React frontend visualizes convergence, price
paths, payoff distribution, and Greeks.

## Structure

```
backend/       FastAPI app, MC pricing engine, pytest suite
frontend/      React (Vite) app, charts via recharts, vitest tests
dashboard/     Static page showing commit activity per contributor (GitHub API)
Jenkinsfile    CI pipeline — auto-triggered on every push
docs/          Setup guides, team plan, git workflow
```

## Running locally

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on `http://127.0.0.1:8000`. Swagger docs at `/docs`.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://127.0.0.1:5173`, calls backend at `http://127.0.0.1:8000`
(override with `VITE_API_BASE` env var).

**Tests**
```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

**Dashboard**
Open `dashboard/index.html` directly in a browser, or serve it with any
static server. Edit `OWNER`/`REPO` at the top of `dashboard/dashboard.js`
first.

## CI/CD

See `docs/JENKINS_SETUP.md` for full setup. Short version: Jenkins pipeline
(`Jenkinsfile`) runs backend pytest + frontend vitest + frontend build on
every commit, auto-triggered via GitHub webhook (or SCM polling fallback).

