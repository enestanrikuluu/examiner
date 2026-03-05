"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type { SessionResult, Grade } from "@/types";

const methodLabels: Record<string, { label: string; color: string }> = {
  deterministic: { label: "Otomatik", color: "bg-blue-100 text-blue-800" },
  llm: { label: "AI", color: "bg-purple-100 text-purple-800" },
  manual: { label: "Manuel", color: "bg-gray-100 text-gray-800" },
  fallback: { label: "Beklemede", color: "bg-yellow-100 text-yellow-800" },
};

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
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Sonuçlar yükleniyor...
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
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
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Score Summary */}
        <div className="rounded-lg bg-white border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Sınav Sonucu</h1>
            {session.status === "submitted" && grades.length === 0 && isInstructor && (
              <button
                onClick={handleGradeSession}
                disabled={grading}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {grading ? "Değerlendiriliyor..." : "Şimdi Değerlendir"}
              </button>
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {session.total_score !== null && (
              <div>
                <p className="text-sm text-gray-500">Toplam Puan</p>
                <p className="text-2xl font-bold text-gray-900">
                  {session.total_score}
                  {session.max_score !== null && (
                    <span className="text-sm font-normal text-gray-500">
                      /{session.max_score}
                    </span>
                  )}
                </p>
              </div>
            )}
            {session.percentage !== null && (
              <div>
                <p className="text-sm text-gray-500">Yüzde</p>
                <p className="text-2xl font-bold text-gray-900">
                  %{session.percentage}
                </p>
              </div>
            )}
            {session.passed !== null && (
              <div>
                <p className="text-sm text-gray-500">Durum</p>
                <p
                  className={`text-2xl font-bold ${
                    session.passed ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {session.passed ? "Geçti" : "Kaldı"}
                </p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-500">Cevaplanan</p>
              <p className="text-2xl font-bold text-gray-900">
                {responses.length}
              </p>
            </div>
          </div>

          {/* Grading method breakdown */}
          {grades.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(methodCounts).map(([method, count]) => {
                const info = methodLabels[method] ?? {
                  label: method,
                  color: "bg-gray-100 text-gray-800",
                };
                return (
                  <span
                    key={method}
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${info.color}`}
                  >
                    {info.label}: {count}
                  </span>
                );
              })}
            </div>
          )}

          {needsManualReview && (
            <div className="mt-4 rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-700">
              Bazı sorular düşük güven skoruyla değerlendirildi ve manuel
              inceleme bekliyor.
            </div>
          )}
        </div>

        {/* Per-response grades */}
        {grades.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">
              Detaylı Sonuçlar
            </h2>
            {responses.map((resp, i) => {
              const grade = gradeMap.get(resp.id);
              if (!grade) return null;
              const method = methodLabels[grade.grading_method] ?? {
                label: grade.grading_method,
                color: "bg-gray-100 text-gray-800",
              };

              return (
                <div
                  key={resp.id}
                  className="rounded-lg border border-gray-200 bg-white p-4 space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-500">
                        Soru {i + 1}
                      </span>
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${method.color}`}
                      >
                        {method.label}
                      </span>
                      {grade.confidence !== null && grade.confidence < 0.7 && (
                        <span className="text-xs text-amber-600">
                          Güven: %{Math.round(grade.confidence * 100)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          grade.is_correct === true
                            ? "bg-green-100 text-green-800"
                            : grade.is_correct === false
                              ? "bg-red-100 text-red-800"
                              : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {grade.score}/{grade.max_score}
                      </span>
                      {isInstructor &&
                        (grade.grading_method === "llm" ||
                          grade.grading_method === "fallback") && (
                          <button
                            onClick={() => handleRegrade(grade.id)}
                            disabled={regrading === grade.id}
                            className="text-xs text-purple-600 hover:text-purple-800 disabled:opacity-50"
                          >
                            {regrading === grade.id
                              ? "Yeniden..."
                              : "Yeniden Değerlendir"}
                          </button>
                        )}
                    </div>
                  </div>

                  {grade.feedback && (
                    <p className="text-sm text-gray-600 whitespace-pre-line">
                      {grade.feedback}
                    </p>
                  )}

                  {grade.rubric_scores &&
                    Array.isArray(grade.rubric_scores) && (
                      <div className="mt-2 space-y-1">
                        <p className="text-xs font-medium text-gray-500">
                          Kriter Puanları:
                        </p>
                        {grade.rubric_scores.map((cs) => (
                          <div
                            key={cs.criterion_id}
                            className="flex items-center justify-between text-xs text-gray-600"
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
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-700">
            Sınav değerlendirme sürecinde. Notlandırma tamamlandığında sonuçlar
            burada görünecektir.
          </div>
        )}

        <Link
          href="/"
          className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Ana Sayfaya Dön
        </Link>
      </div>
    </div>
  );
}
