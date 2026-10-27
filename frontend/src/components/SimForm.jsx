import React from "react";

const FIELDS = [
  { name: "ticker", label: "Ticker (optional)", type: "text" },
  { name: "spot", label: "Spot Price", type: "number" },
  { name: "strike", label: "Strike", type: "number" },
  { name: "vol", label: "Volatility (e.g. 0.2)", type: "number" },
  { name: "rate", label: "Risk-free Rate", type: "number" },
  { name: "days", label: "Days to Expiry", type: "number" },
  { name: "sims", label: "Simulations", type: "number" },
];

export default function SimForm({ values, onChange, onSubmit, loading, onFetchTicker }) {
  return (
    <div className="panel">
      <div className="grid">
        {FIELDS.map((f) => (
          <div key={f.name}>
            <label>{f.label}</label>
            <input
              type={f.type}
              value={values[f.name] ?? ""}
              onChange={(e) => onChange(f.name, e.target.value)}
            />
          </div>
        ))}

        <div>
          <label>Option Type</label>
          <select
            value={values.option_type}
            onChange={(e) => onChange("option_type", e.target.value)}
          >
            <option value="call">Call</option>
            <option value="put">Put</option>
          </select>
        </div>

        <div>
          <label>Option Style</label>
          <select
            value={values.style}
            onChange={(e) => onChange("style", e.target.value)}
          >
            <option value="european">European</option>
            <option value="asian">Asian</option>
            <option value="barrier">Barrier</option>
          </select>
        </div>

        {values.style === "barrier" && (
          <>
            <div>
              <label>Barrier Level</label>
              <input
                type="number"
                value={values.barrier ?? ""}
                onChange={(e) => onChange("barrier", e.target.value)}
              />
            </div>
            <div>
              <label>Barrier Type</label>
              <select
                value={values.barrier_type ?? "up-and-out"}
                onChange={(e) => onChange("barrier_type", e.target.value)}
              >
                <option value="up-and-out">Up-and-Out</option>
                <option value="down-and-out">Down-and-Out</option>
                <option value="up-and-in">Up-and-In</option>
                <option value="down-and-in">Down-and-In</option>
              </select>
            </div>
          </>
        )}
      </div>

      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button
          type="button"
          onClick={onFetchTicker}
          disabled={!values.ticker || loading}
        >
          Fetch Ticker Data
        </button>
        <button type="button" onClick={onSubmit} disabled={loading}>
          {loading ? "Simulating..." : "Run Simulation"}
        </button>
      </div>
    </div>
  );
}
