"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";

interface SessionItem {
  id: string;
  template_id: string;
  status: string;
  started_at: string | null;
  submitted_at: string | null;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  passed: boolean | null;
  created_at: string;
}

interface TemplateInfo {
  id: string;
  title: string;
  question_count: number;
  pass_score: number;
}

const statusLabels: Record<string, { label: string; color: string; bg: string }> = {
  created: { label: "Oluşturuldu", color: "var(--text-muted)", bg: "var(--border-light)" },
  in_progress: { label: "Devam Ediyor", color: "var(--warning)", bg: "var(--warning-light)" },
  submitted: { label: "Tamamlandı", color: "var(--accent)", bg: "var(--accent-light)" },
  graded: { label: "Notlandırıldı", color: "var(--special)", bg: "var(--special-light)" },
};

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function MyExamsPage() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [templates, setTemplates] = useState<Record<string, TemplateInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [sessData, tmplData] = await Promise.all([
          api.get<{ items: SessionItem[]; total: number }>("/sessions?page_size=50"),
          api.get<{ items: TemplateInfo[] }>("/templates"),
        ]);
        setSessions(sessData.items);
        const map: Record<string, TemplateInfo> = {};
        for (const t of tmplData.items) {
          map[t.id] = t;
        }
        setTemplates(map);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Yüklenemedi");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p style={{ color: "var(--text-muted)" }}>Yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <p style={{ color: "var(--danger)" }}>{error}</p>
      </div>
    );
  }

  const submitted = sessions.filter((s) => s.status === "submitted" || s.status === "graded");
  const inProgress = sessions.filter((s) => s.status === "in_progress" || s.status === "created");

  return (
    <div className="space-y-8">
      <div>
        <h1
          className="text-3xl font-bold tracking-tight"
          style={{
            fontFamily: "var(--font-playfair), Georgia, serif",
            color: "var(--text-primary)",
          }}
        >
          Sınavlarım
        </h1>
        <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
          Girdiğiniz sınavlar ve sonuçlarınız.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M8 0L9.8 6.2L16 8L9.8 9.8L8 16L6.2 9.8L0 8L6.2 6.2L8 0Z"
            fill="var(--border)"
          />
        </svg>
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
      </div>

      {sessions.length === 0 ? (
        <div
          className="rounded-lg border p-12 text-center"
          style={{
            backgroundColor: "var(--card)",
            borderColor: "var(--border-light)",
          }}
        >
          <p style={{ color: "var(--text-muted)" }}>Henüz bir sınava girmediniz.</p>
          <Link
            href="/exams"
            className="inline-block mt-4 px-4 py-2 rounded-md text-sm font-medium text-white"
            style={{ backgroundColor: "var(--accent)" }}
          >
            Sınavlara Göz At
          </Link>
        </div>
      ) : (
        <>
          {inProgress.length > 0 && (
            <div className="space-y-3">
              <h2
                className="text-lg font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                Devam Eden Sınavlar
              </h2>
              <div className="space-y-2">
                {inProgress.map((s) => (
                  <SessionCard key={s.id} session={s} template={templates[s.template_id]} />
                ))}
              </div>
            </div>
          )}

          {submitted.length > 0 && (
            <div className="space-y-3">
              <h2
                className="text-lg font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                Tamamlanan Sınavlar
              </h2>
              <div className="space-y-2">
                {submitted.map((s) => (
                  <SessionCard key={s.id} session={s} template={templates[s.template_id]} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SessionCard({
  session: s,
  template,
}: {
  session: SessionItem;
  template?: TemplateInfo;
}) {
  const st = statusLabels[s.status] ?? statusLabels.created;
  const isFinished = s.status === "submitted" || s.status === "graded";
  const href = isFinished ? `/exam/${s.id}/result` : `/exam/${s.id}`;

  return (
    <Link
      href={href}
      className="block rounded-lg border p-5 transition-all"
      style={{
        backgroundColor: "var(--card)",
        borderColor: "var(--border-light)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--card-hover)";
        e.currentTarget.style.borderColor = "var(--border)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "var(--card)";
        e.currentTarget.style.borderColor = "var(--border-light)";
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h3
              className="font-semibold truncate"
              style={{
                fontFamily: "var(--font-playfair), Georgia, serif",
                color: "var(--text-primary)",
              }}
            >
              {template?.title ?? "Sınav"}
            </h3>
            <span
              className="px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap"
              style={{ backgroundColor: st.bg, color: st.color }}
            >
              {st.label}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
            <span>{formatDate(s.submitted_at ?? s.started_at ?? s.created_at)}</span>
            {template && <span>{template.question_count} soru</span>}
          </div>
        </div>

        {isFinished && s.percentage !== null && (
          <div className="flex items-center gap-4 ml-4">
            <div className="text-right">
              <div
                className="text-2xl font-bold"
                style={{
                  fontFamily: "var(--font-playfair), Georgia, serif",
                  color: s.passed ? "var(--success)" : "var(--danger)",
                }}
              >
                %{Math.round(s.percentage)}
              </div>
              <div
                className="text-xs font-medium"
                style={{ color: s.passed ? "var(--success)" : "var(--danger)" }}
              >
                {s.passed ? "Geçti" : "Kaldı"}
              </div>
            </div>
            <div
              className="flex items-center justify-center w-10 h-10 rounded-full"
              style={{
                backgroundColor: s.passed ? "var(--success-light)" : "var(--danger-light)",
                color: s.passed ? "var(--success)" : "var(--danger)",
              }}
            >
              {s.passed ? (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M4 10l4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 5l10 10M15 5l-10 10" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
          </div>
        )}

        {!isFinished && (
          <div className="ml-4">
            <span
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium text-white"
              style={{ backgroundColor: "var(--accent)" }}
            >
              Devam Et →
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}
