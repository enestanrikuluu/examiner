"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type {
  DashboardData,
  ExamTemplate,
  ExamTemplateListResponse,
  ScoreDistribution,
  ItemAnalysis,
} from "@/types";

// --- Stat Card ---

function StatCard({
  label,
  value,
  sub,
  color = "blue",
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: "blue" | "green" | "purple" | "amber" | "red";
}) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-red-50 text-red-600",
  };
  return (
    <div className={`rounded-lg p-4 ${colors[color]}`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs mt-1 opacity-75">{sub}</p>}
    </div>
  );
}

// --- Score Histogram ---

function ScoreHistogram({ distribution }: { distribution: ScoreDistribution }) {
  if (distribution.distribution.length === 0) return null;

  const maxCount = Math.max(...distribution.distribution.map((b) => b.count), 1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        Puan Dagilimi
      </h3>
      <div className="flex items-end gap-1 h-32">
        {distribution.distribution.map((bucket, i) => {
          const height = (bucket.count / maxCount) * 100;
          return (
            <div
              key={i}
              className="flex-1 flex flex-col items-center gap-1"
            >
              <span className="text-[10px] text-gray-400">
                {bucket.count > 0 ? bucket.count : ""}
              </span>
              <div
                className="w-full bg-blue-400 rounded-t"
                style={{ height: `${Math.max(height, 2)}%` }}
                title={`%${bucket.range_start}-${bucket.range_end}: ${bucket.count} oturum`}
              />
              <span className="text-[9px] text-gray-400">
                {bucket.range_start.toFixed(0)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Difficulty Table ---

function DifficultItems({ items }: { items: ItemAnalysis["items"] }) {
  if (items.length === 0) return null;

  const typeLabels: Record<string, string> = {
    mcq: "CS",
    true_false: "DY",
    numeric: "Say",
    short_answer: "KY",
    long_form: "UC",
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        En Zor Sorular
      </h3>
      <div className="space-y-2">
        {items.slice(0, 10).map((item) => (
          <div
            key={item.question_id}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="inline-flex rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600 flex-shrink-0">
                {typeLabels[item.question_type] ?? item.question_type}
              </span>
              <span className="text-gray-700 truncate">
                {item.stem_preview}
              </span>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0 ml-3">
              <span className="text-gray-400 text-xs">
                {item.response_count} cevap
              </span>
              <span
                className={`font-medium ${
                  item.p_value < 0.3
                    ? "text-red-600"
                    : item.p_value < 0.7
                      ? "text-amber-600"
                      : "text-green-600"
                }`}
              >
                %{(item.p_value * 100).toFixed(0)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Performance Chart (Simple SVG) ---

function PerformanceChart({
  points,
}: {
  points: DashboardData["recent_scores"];
}) {
  if (points.length < 2) return null;

  const width = 600;
  const height = 150;
  const pad = { top: 15, right: 10, bottom: 25, left: 40 };
  const cW = width - pad.left - pad.right;
  const cH = height - pad.top - pad.bottom;

  const values = points.map((p) => p.mean_percentage ?? 0);
  const minV = Math.min(...values) - 5;
  const maxV = Math.max(...values) + 5;
  const range = Math.max(maxV - minV, 10);

  const xScale = (i: number) => pad.left + (i / (points.length - 1)) * cW;
  const yScale = (v: number) => pad.top + (1 - (v - minV) / range) * cH;

  const linePath = points
    .map((p, i) => {
      const x = xScale(i);
      const y = yScale(p.mean_percentage ?? 0);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        Performans Seyri (Son 30 Gun)
      </h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {/* Grid */}
        {[0, 25, 50, 75, 100]
          .filter((v) => v >= minV && v <= maxV)
          .map((v) => (
            <g key={v}>
              <line
                x1={pad.left}
                y1={yScale(v)}
                x2={width - pad.right}
                y2={yScale(v)}
                stroke="#f3f4f6"
              />
              <text
                x={pad.left - 5}
                y={yScale(v) + 4}
                textAnchor="end"
                className="text-[10px] fill-gray-400"
              >
                %{v}
              </text>
            </g>
          ))}
        {/* Line */}
        <path d={linePath} fill="none" stroke="#3b82f6" strokeWidth={2} />
        {/* Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={xScale(i)}
            cy={yScale(p.mean_percentage ?? 0)}
            r={3}
            fill="#3b82f6"
          />
        ))}
        {/* X labels (first, mid, last) */}
        {[0, Math.floor(points.length / 2), points.length - 1].map((i) => (
          <text
            key={i}
            x={xScale(i)}
            y={height - 5}
            textAnchor="middle"
            className="text-[9px] fill-gray-400"
          >
            {points[i]?.date.slice(5) ?? ""}
          </text>
        ))}
      </svg>
    </div>
  );
}

// --- Main Analytics Page ---

export default function AnalyticsPage() {
  const { user } = useAuthStore();
  const [templates, setTemplates] = useState<ExamTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [scoreDist, setScoreDist] = useState<ScoreDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const isInstructor =
    user?.role === "instructor" || user?.role === "admin";

  // Load templates
  useEffect(() => {
    api
      .get<ExamTemplateListResponse>("/templates")
      .then((data) => {
        setTemplates(data.items);
        if (data.items.length > 0) {
          setSelectedTemplate(data.items[0].id);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Load dashboard data when template changes
  useEffect(() => {
    if (!selectedTemplate) return;

    setLoading(true);
    const params = new URLSearchParams();
    if (selectedTemplate) params.set("template_id", selectedTemplate);

    Promise.all([
      api.get<DashboardData>(`/analytics/dashboard?${params}`),
      isInstructor
        ? api.get<ScoreDistribution>(
            `/analytics/scores/${selectedTemplate}`
          )
        : Promise.resolve(null),
    ])
      .then(([dash, dist]) => {
        setDashboard(dash);
        setScoreDist(dist);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedTemplate, isInstructor]);

  async function handleExport(format: "csv" | "pdf") {
    if (!selectedTemplate) return;
    setExporting(true);
    try {
      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/analytics/export/${format}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
          },
          body: JSON.stringify({
            template_id: selectedTemplate,
            format,
            include_grades: true,
          }),
        }
      );
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `export_${selectedTemplate}.${format === "csv" ? "csv" : "txt"}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      // handled
    } finally {
      setExporting(false);
    }
  }

  if (loading && !dashboard) {
    return (
      <div className="text-center py-12 text-gray-500">Yukleniyor...</div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analiz</h1>
          <p className="mt-1 text-sm text-gray-600">
            Sinav performansi ve soru analizi
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Template Selector */}
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>

          {/* Export Buttons */}
          {isInstructor && selectedTemplate && (
            <>
              <button
                onClick={() => handleExport("csv")}
                disabled={exporting}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                CSV
              </button>
              <button
                onClick={() => handleExport("pdf")}
                disabled={exporting}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Rapor
              </button>
            </>
          )}
        </div>
      </div>

      {dashboard && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Toplam Oturum"
              value={dashboard.session_summary.total_sessions}
              color="blue"
            />
            <StatCard
              label="Notlanan"
              value={dashboard.session_summary.graded}
              color="green"
            />
            <StatCard
              label="Ortalama Puan"
              value={
                dashboard.session_summary.avg_percentage != null
                  ? `%${dashboard.session_summary.avg_percentage}`
                  : "-"
              }
              color="purple"
            />
            <StatCard
              label="Gecme Orani"
              value={
                dashboard.session_summary.pass_rate != null
                  ? `%${dashboard.session_summary.pass_rate}`
                  : "-"
              }
              color="amber"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Over Time */}
            <PerformanceChart points={dashboard.recent_scores} />

            {/* Score Distribution */}
            {scoreDist && <ScoreHistogram distribution={scoreDist} />}
          </div>

          {/* Difficulty + AI Costs */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DifficultItems items={dashboard.top_difficult_items} />

            {/* AI Costs */}
            {dashboard.ai_cost_summary && (
              <div className="rounded-lg border border-gray-200 bg-white p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">
                  AI Maliyetleri (Son 30 Gun)
                </h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <StatCard
                    label="Toplam Maliyet"
                    value={`$${dashboard.ai_cost_summary.total_cost_usd.toFixed(4)}`}
                    color="red"
                  />
                  <StatCard
                    label="Toplam Cagri"
                    value={dashboard.ai_cost_summary.total_calls}
                    color="purple"
                  />
                </div>
                {dashboard.ai_cost_summary.by_task.length > 0 && (
                  <div className="space-y-2">
                    {dashboard.ai_cost_summary.by_task.map((t) => (
                      <div
                        key={t.task_type}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-gray-600 capitalize">
                          {t.task_type}
                        </span>
                        <div className="flex items-center gap-4">
                          <span className="text-gray-400">
                            {t.call_count} cagri
                          </span>
                          <span className="font-medium text-gray-900">
                            ${t.total_cost_usd.toFixed(4)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
