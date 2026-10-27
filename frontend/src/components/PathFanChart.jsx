import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

// sample_paths: array of arrays (each inner array = one path's prices over time)
export default function PathFanChart({ paths }) {
  if (!paths || paths.length === 0) return null;

  // reshape into recharts-friendly format: [{step: 0, path0: x, path1: y, ...}, ...]
  const steps = paths[0].length;
  const chartData = Array.from({ length: steps }, (_, step) => {
    const point = { step };
    paths.slice(0, 30).forEach((p, i) => {
      point[`p${i}`] = p[step];
    });
    return point;
  });

  return (
    <div className="panel">
      <h2 style={{ fontSize: "1.1rem" }}>Sample Simulated Paths</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="step" stroke="#9aa0ac" />
          <YAxis stroke="#9aa0ac" />
          {paths.slice(0, 30).map((_, i) => (
            <Line
              key={i}
              type="monotone"
              dataKey={`p${i}`}
              stroke="#4f7cff"
              strokeOpacity={0.35}
              dot={false}
              strokeWidth={1}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
