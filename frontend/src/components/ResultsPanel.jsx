import React from "react";

export default function ResultsPanel({ result }) {
  if (!result) return null;

  const { price, std_err, greeks, bs_benchmark } = result;

  return (
    <div className="panel">
      <h2 style={{ fontSize: "1.1rem" }}>Results</h2>
      <div className="stat-row">
        <div className="stat">
          <div className="value">${price.toFixed(4)}</div>
          <div className="label">MC Price (±{std_err.toFixed(4)})</div>
        </div>

        {bs_benchmark && (
          <div className="stat">
            <div className="value">${bs_benchmark.price.toFixed(4)}</div>
            <div className="label">Black-Scholes Price</div>
          </div>
        )}

        <div className="stat">
          <div className="value">{greeks.delta.toFixed(4)}</div>
          <div className="label">Delta</div>
        </div>
        <div className="stat">
          <div className="value">{greeks.gamma.toFixed(4)}</div>
          <div className="label">Gamma</div>
        </div>
        <div className="stat">
          <div className="value">{greeks.vega.toFixed(4)}</div>
          <div className="label">Vega</div>
        </div>
      </div>
    </div>
  );
}
