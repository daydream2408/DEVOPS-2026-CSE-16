import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function PayoffHistogram({ distribution }) {
  if (!distribution || distribution.length === 0) return null;

  const chartData = distribution.map((bin) => ({
    range: `${bin.binStart.toFixed(1)}`,
    count: bin.count,
  }));

  return (
    <div className="panel">
      <h2 style={{ fontSize: "1.1rem" }}>Payoff Distribution</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="range" stroke="#9aa0ac" />
          <YAxis stroke="#9aa0ac" />
          <Tooltip
            contentStyle={{ background: "#171923", border: "1px solid #2a2d3a" }}
          />
          <Bar dataKey="count" fill="#4f7cff" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
