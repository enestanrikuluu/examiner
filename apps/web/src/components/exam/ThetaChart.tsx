"use client";

import type { ThetaHistoryEntry } from "@/types";

interface ThetaChartProps {
  history: ThetaHistoryEntry[];
  height?: number;
}

export default function ThetaChart({ history, height = 200 }: ThetaChartProps) {
  if (history.length === 0) return null;

  const width = 600;
  const padding = { top: 20, right: 40, bottom: 30, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Data ranges
  const thetas = history.map((h) => h.theta);
  const ses = history.map((h) => h.se);
  const minTheta = Math.min(...thetas) - 0.5;
  const maxTheta = Math.max(...thetas) + 0.5;
  const yRange = Math.max(maxTheta - minTheta, 1);

  // Scale helpers
  const xScale = (step: number) =>
    padding.left + ((step - 1) / Math.max(history.length - 1, 1)) * chartW;
  const yScale = (theta: number) =>
    padding.top + (1 - (theta - minTheta) / yRange) * chartH;

  // Build line path
  const linePath = history
    .map((h, i) => {
      const x = xScale(h.step);
      const y = yScale(h.theta);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  // Build SE band
  const upperBand = history
    .map((h) => {
      const x = xScale(h.step);
      const y = yScale(h.theta + h.se);
      return `${x},${y}`;
    })
    .join(" ");
  const lowerBand = [...history]
    .reverse()
    .map((h) => {
      const x = xScale(h.step);
      const y = yScale(h.theta - h.se);
      return `${x},${y}`;
    })
    .join(" ");

  // Y-axis ticks
  const yTicks: number[] = [];
  const tickStep = yRange <= 2 ? 0.5 : yRange <= 5 ? 1 : 2;
  for (
    let t = Math.ceil(minTheta / tickStep) * tickStep;
    t <= maxTheta;
    t += tickStep
  ) {
    yTicks.push(t);
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full max-w-[600px] mx-auto"
      role="img"
      aria-label="Theta estimation chart"
    >
      {/* Grid lines */}
      {yTicks.map((tick) => (
        <g key={tick}>
          <line
            x1={padding.left}
            y1={yScale(tick)}
            x2={width - padding.right}
            y2={yScale(tick)}
            stroke="#e5e7eb"
            strokeWidth={1}
          />
          <text
            x={padding.left - 8}
            y={yScale(tick) + 4}
            textAnchor="end"
            className="text-[10px] fill-gray-400"
          >
            {tick.toFixed(1)}
          </text>
        </g>
      ))}

      {/* X-axis labels */}
      {history.map((h) => (
        <text
          key={h.step}
          x={xScale(h.step)}
          y={height - 5}
          textAnchor="middle"
          className="text-[10px] fill-gray-400"
        >
          {h.step}
        </text>
      ))}

      {/* SE band */}
      <polygon
        points={`${upperBand} ${lowerBand}`}
        fill="rgba(59, 130, 246, 0.1)"
        stroke="none"
      />

      {/* Theta line */}
      <path d={linePath} fill="none" stroke="#3b82f6" strokeWidth={2} />

      {/* Data points */}
      {history.map((h) => (
        <circle
          key={h.step}
          cx={xScale(h.step)}
          cy={yScale(h.theta)}
          r={4}
          fill={h.is_correct ? "#22c55e" : "#ef4444"}
          stroke="white"
          strokeWidth={1.5}
        />
      ))}

      {/* Zero line */}
      {minTheta <= 0 && maxTheta >= 0 && (
        <line
          x1={padding.left}
          y1={yScale(0)}
          x2={width - padding.right}
          y2={yScale(0)}
          stroke="#9ca3af"
          strokeWidth={1}
          strokeDasharray="4 4"
        />
      )}

      {/* Axis labels */}
      <text
        x={padding.left - 35}
        y={height / 2}
        textAnchor="middle"
        transform={`rotate(-90, ${padding.left - 35}, ${height / 2})`}
        className="text-[11px] fill-gray-500 font-medium"
      >
        {"\u03B8"}
      </text>
      <text
        x={width / 2}
        y={height - 2}
        textAnchor="middle"
        className="text-[11px] fill-gray-500 font-medium"
      >
        Soru
      </text>

      {/* SE label for last point */}
      {history.length > 0 && (
        <text
          x={xScale(history[history.length - 1].step) + 8}
          y={yScale(history[history.length - 1].theta) + 4}
          className="text-[10px] fill-blue-600 font-medium"
        >
          SE: {ses[ses.length - 1].toFixed(3)}
        </text>
      )}
    </svg>
  );
}
