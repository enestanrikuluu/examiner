"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type { SessionResult, Grade } from "@/types";

const methodLabels: Record<string, { label: string; accentClass?: string }> = {
  deterministic: { label: "Otomatik", accentClass: "deterministic" },
  llm: { label: "AI", accentClass: "llm" },
  manual: { label: "Manuel", accentClass: "manual" },
  fallback: { label: "Beklemede", accentClass: "fallback" },
};

function getMethodBadgeStyle(method: string | undefined) {
  switch (method) {
    case "deterministic":
      return {
        backgroundColor: "var(--accent-light)",
        color: "var(--accent)",
      };
    case "llm":
      return {
        backgroundColor: "var(--special-light)",
        color: "var(--special)",
      };
    case "manual":
      return {
        backgroundColor: "#E8DFD0",
        color: "var(--text-muted)",
      };
    case "fallback":
      return {
        backgroundColor: "var(--warning-light)",
        color: "var(--warning)",
      };
    default:
      return {
        backgroundColor: "var(--border-light)",
        color: "var(--text-secondary)",
      };
  }
}

function getScoreBadgeStyle(isCorrect: boolean | null) {
  if (isCorrect === true) {
    return {
      backgroundColor: "var(--success-light)",
      color: "var(--success)",
    };
  }
  if (isCorrect === false) {
    return {
      backgroundColor: "var(--danger-light)",
      color: "var(--danger)",
    };
  }
  return {
    backgroundColor: "var(--border-light)",
    color: "var(--text-secondary)",
  };
}

export default function SessionResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user } = useAuthStore();
  const [result, setResult] = useState<SessionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [grading, setGrading] = useState(false);
  const [regrading, setRegrading] = useState<string | null>(null);

  const isInstructor =
    user?.role === "instructor" || user?.role === "admin";

  useEffect(() => {
    loadResult();
  }, [sessionId]);

  async function loadResult() {
    try {
      const data = await api.get<SessionResult>(
        `/sessions/${sessionId}/result`
      );
      setResult(data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }

  async function handleGradeSession() {
    setGrading(true);
    try {
      await api.post(`/grading/sessions/${sessionId}/grade`);
      await loadResult();
    } catch {
      // handled
    } finally {
      setGrading(false);
    }
  }

  async function handleRegrade(gradeId: string) {
    setRegrading(gradeId);
    try {
      const updated = await api.post<Grade>(
        `/grading/grades/${gradeId}/regrade`
      );
      // Update the grade in local state
      setResult((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          grades: prev.grades.map((g) =>
            g.id === gradeId ? updated : g
          ),
        };
      });
    } catch {
      // handled
    } finally {
      setRegrading(null);
    }
  }

  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: "var(--background)", color: "var(--text-muted)" }}
      >
        Sonuçlar yükleniyor...
      </div>
    );
  }

  if (!result) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: "var(--background)", color: "var(--text-muted)" }}
      >
        Sonuç bulunamadı.
      </div>
    );
  }

  const { session, responses, grades } = result;
  const gradeMap = new Map(grades.map((g) => [g.response_id, g]));

  // Count by method
  const methodCounts: Record<string, number> = {};
  for (const g of grades) {
    const method = g.grading_method || "unknown";
    methodCounts[method] = (methodCounts[method] || 0) + 1;
  }

  const needsManualReview = grades.some(
    (g) => g.grading_method === "fallback"
  );

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "var(--background)" }}
    >
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Score Summary */}
        <div
          className="rounded-lg border p-6"
          style={{
            backgroundColor: "var(--card)",
            borderColor: "var(--border)",
          }}
        >
          <div className="flex items-center justify-between">
            <h1
              className="text-2xl font-bold"
              style={{
                color: "var(--text-primary)",
                fontFamily: 'var(--font-playfair), Georgia, serif',
              }}
            >
              Sınav Sonucu
            </h1>
            {session.status === "submitted" && grades.length === 0 && isInstructor && (
              <button
                onClick={handleGradeSession}
                disabled={grading}
                className="rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
                style={{
                  backgroundColor: grading ? "var(--accent)" : "var(--accent)",
                  color: "#FFFAF5",
                }}
                onMouseEnter={(e) => {
                  if (!grading) e.currentTarget.style.backgroundColor = "var(--accent-hover)";
                }}
                onMouseLeave={(e) => {
                  if (!grading) e.currentTarget.style.backgroundColor = "var(--accent)";
                }}
              >
                {grading ? "Değerlendiriliyor..." : "Şimdi Değerlendir"}
              </button>
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {session.total_score !== null && (
              <div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Toplam Puan
                </p>
                <p
                  className="text-2xl font-bold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {session.total_score}
                  {session.max_score !== null && (
                    <span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}>
                      /{session.max_score}
                    </span>
                  )}
                </p>
              </div>
            )}
            {session.percentage !== null && (
              <div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Yüzde
                </p>
                <p
                  className="text-2xl font-bold"
                  style={{ color: "var(--text-primary)" }}
                >
                  %{session.percentage}
                </p>
              </div>
            )}
            {session.passed !== null && (
              <div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Durum
                </p>
                <p
                  className="text-2xl font-bold"
                  style={{
                    color: session.passed ? "var(--success)" : "var(--danger)",
                  }}
                >
                  {session.passed ? "Geçti" : "Kaldı"}
                </p>
              </div>
            )}
            <div>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                Cevaplanan
              </p>
              <p
                className="text-2xl font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                {responses.length}
              </p>
            </div>
          </div>

          {/* Grading method breakdown */}
          {grades.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(methodCounts).map(([method, count]) => {
                const style = getMethodBadgeStyle(method);
                return (
                  <span
                    key={method}
                    className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    style={style}
                  >
                    {methodLabels[method]?.label || method}: {count}
                  </span>
                );
              })}
            </div>
          )}

          {needsManualReview && (
            <div
              className="mt-4 rounded-md border p-3 text-sm"
              style={{
                backgroundColor: "var(--warning-light)",
                borderColor: "var(--warning)",
                color: "var(--warning)",
              }}
            >
              Bazı sorular düşük güven skoruyla değerlendirildi ve manuel
              inceleme bekliyor.
            </div>
          )}
        </div>

        {/* Per-response grades */}
        {grades.length > 0 && (
          <div className="space-y-3">
            <h2
              className="text-lg font-semibold"
              style={{
                color: "var(--text-primary)",
                fontFamily: 'var(--font-playfair), Georgia, serif',
              }}
            >
              Detaylı Sonuçlar
            </h2>
            {responses.map((resp, i) => {
              const grade = gradeMap.get(resp.id);
              if (!grade) return null;

              return (
                <div
                  key={resp.id}
                  className="rounded-lg border p-4 space-y-2"
                  style={{
                    backgroundColor: "var(--card)",
                    borderColor: "var(--border)",
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-sm font-medium"
                        style={{ color: "var(--text-muted)" }}
                      >
                        Soru {i + 1}
                      </span>
                      <span
                        className="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                        style={getMethodBadgeStyle(grade.grading_method)}
                      >
                        {methodLabels[grade.grading_method]?.label || grade.grading_method}
                      </span>
                      {grade.confidence !== null && grade.confidence < 0.7 && (
                        <span
                          className="text-xs"
                          style={{ color: "var(--warning)" }}
                        >
                          Güven: %{Math.round(grade.confidence * 100)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold"
                        style={getScoreBadgeStyle(grade.is_correct)}
                      >
                        {grade.score}/{grade.max_score}
                      </span>
                      {isInstructor &&
                        (grade.grading_method === "llm" ||
                          grade.grading_method === "fallback") && (
                          <button
                            onClick={() => handleRegrade(grade.id)}
                            disabled={regrading === grade.id}
                            className="text-xs transition-colors disabled:opacity-50"
                            style={{
                              color: "var(--special)",
                            }}
                            onMouseEnter={(e) => {
                              if (regrading !== grade.id) {
                                e.currentTarget.style.opacity = "0.7";
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (regrading !== grade.id) {
                                e.currentTarget.style.opacity = "1";
                              }
                            }}
                          >
                            {regrading === grade.id
                              ? "Yeniden..."
                              : "Yeniden Değerlendir"}
                          </button>
                        )}
                    </div>
                  </div>

                  {grade.feedback && (
                    <p
                      className="text-sm whitespace-pre-line"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {grade.feedback}
                    </p>
                  )}

                  {grade.rubric_scores &&
                    Array.isArray(grade.rubric_scores) && (
                      <div className="mt-2 space-y-1">
                        <p
                          className="text-xs font-medium"
                          style={{ color: "var(--text-muted)" }}
                        >
                          Kriter Puanları:
                        </p>
                        {grade.rubric_scores.map((cs) => (
                          <div
                            key={cs.criterion_id}
                            className="flex items-center justify-between text-xs"
                            style={{ color: "var(--text-secondary)" }}
                          >
                            <span>{cs.criterion_id}</span>
                            <span>
                              {cs.score}/{cs.max_score}
                              {cs.feedback && ` - ${cs.feedback}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                </div>
              );
            })}
          </div>
        )}

        {grades.length === 0 && session.status === "submitted" && (
          <div
            className="rounded-lg border p-4 text-sm"
            style={{
              backgroundColor: "var(--warning-light)",
              borderColor: "var(--warning)",
              color: "var(--warning)",
            }}
          >
            Sınav değerlendirme sürecinde. Notlandırma tamamlandığında sonuçlar
            burada görünecektir.
          </div>
        )}

        <Link
          href="/"
          className="inline-block rounded-md px-4 py-2 text-sm font-medium transition-colors"
          style={{
            backgroundColor: "var(--accent)",
            color: "#FFFAF5",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--accent-hover)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--accent)";
          }}
        >
          Ana Sayfaya Dön
        </Link>
      </div>
    </div>
  );
}
