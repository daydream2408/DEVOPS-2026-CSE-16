import React, { useState } from "react";
import SimForm from "./components/SimForm.jsx";
import ResultsPanel from "./components/ResultsPanel.jsx";
import ConvergenceChart from "./components/ConvergenceChart.jsx";
import PathFanChart from "./components/PathFanChart.jsx";
import PayoffHistogram from "./components/PayoffHistogram.jsx";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const DEFAULT_VALUES = {
  ticker: "",
  spot: 100,
  strike: 105,
  vol: 0.2,
  rate: 0.05,
  days: 30,
  sims: 10000,
  option_type: "call",
  style: "european",
  barrier: 120,
  barrier_type: "up-and-out",
};

export default function App() {
  const [values, setValues] = useState(DEFAULT_VALUES);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(name, value) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function fetchTicker() {
    if (!values.ticker) return;
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/ticker-info?ticker=${encodeURIComponent(values.ticker)}`
      );
      if (!res.ok) throw new Error((await res.json()).detail || "Ticker fetch failed");
      const data = await res.json();
      setValues((prev) => ({ ...prev, spot: data.spot, vol: data.volatility }));
    } catch (e) {
      setError(e.message);
    }
  }

  async function runSimulation() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        spot: Number(values.spot),
        strike: Number(values.strike),
        vol: Number(values.vol),
        rate: Number(values.rate),
        days: Number(values.days),
        sims: Number(values.sims),
        steps: 100,
        option_type: values.option_type,
        style: values.style,
        barrier: values.style === "barrier" ? Number(values.barrier) : null,
        barrier_type: values.style === "barrier" ? values.barrier_type : null,
      };

      const res = await fetch(`${API_BASE}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errBody = await res.json();
        throw new Error(errBody.detail || "Simulation failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>Monte Carlo Options Pricing &amp; Risk Simulator</h1>

      <SimForm
        values={values}
        onChange={handleChange}
        onSubmit={runSimulation}
        onFetchTicker={fetchTicker}
        loading={loading}
      />

      {error && (
        <div className="panel error">Error: {error}</div>
      )}

      <ResultsPanel result={result} />
      {result && <ConvergenceChart data={result.convergence} />}
      {result && <PathFanChart paths={result.sample_paths} />}
      {result && <PayoffHistogram distribution={result.payoff_distribution} />}
    </div>
  );
}
