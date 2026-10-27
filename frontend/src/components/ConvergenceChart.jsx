import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function ConvergenceChart({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="panel">
      <h2 style={{ fontSize: "1.1rem" }}>Price Convergence</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="sims" stroke="#9aa0ac" />
          <YAxis stroke="#9aa0ac" />
          <Tooltip
            contentStyle={{ background: "#171923", border: "1px solid #2a2d3a" }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#4f7cff"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
