"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { SessionResult } from "@/types";

export default function SessionResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [result, setResult] = useState<SessionResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
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
    load();
  }, [sessionId]);

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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <div className="rounded-lg bg-white border border-gray-200 p-6">
          <h1 className="text-2xl font-bold text-gray-900">Sınav Sonucu</h1>

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
        </div>

        {/* Per-response grades */}
        {grades.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">
              Detaylı Sonuçlar
            </h2>
            {responses.map((resp, i) => {
              const grade = gradeMap.get(resp.id);
              return (
                <div
                  key={resp.id}
                  className="rounded-lg border border-gray-200 bg-white p-4"
                >
                  <div className="flex items-start justify-between">
                    <span className="text-sm font-medium text-gray-500">
                      Soru {i + 1}
                    </span>
                    {grade && (
                      <div className="text-right">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            grade.is_correct
                              ? "bg-green-100 text-green-800"
                              : grade.is_correct === false
                                ? "bg-red-100 text-red-800"
                                : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {grade.score}/{grade.max_score}
                        </span>
                      </div>
                    )}
                  </div>
                  {grade?.feedback && (
                    <p className="mt-2 text-sm text-gray-600">
                      {grade.feedback}
                    </p>
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
