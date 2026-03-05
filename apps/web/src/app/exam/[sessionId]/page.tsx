"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type {
  ExamSession,
  QuestionItem,
  QuestionItemListResponse,
} from "@/types";

export default function ExamSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [session, setSession] = useState<ExamSession | null>(null);
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        let sess = await api.get<ExamSession>(`/sessions/${sessionId}`);

        if (sess.status === "created") {
          sess = await api.post<ExamSession>(
            `/sessions/${sessionId}/start`
          );
        }

        if (sess.status === "submitted" || sess.status === "graded") {
          router.push(`/exam/${sessionId}/result`);
          return;
        }

        setSession(sess);

        const qData = await api.get<QuestionItemListResponse>(
          `/templates/${sess.template_id}/questions`
        );

        // Reorder questions based on session.question_order
        if (sess.question_order) {
          const qMap = new Map(qData.items.map((q) => [q.id, q]));
          const ordered = sess.question_order
            .map((id) => qMap.get(id))
            .filter((q): q is QuestionItem => q !== undefined);
          setQuestions(ordered);
        } else {
          setQuestions(qData.items);
        }
      } catch {
        // handled
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId, router]);

  async function saveAnswer(questionId: string, answer: unknown) {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
    try {
      await api.post(`/sessions/${sessionId}/responses`, {
        question_id: questionId,
        answer,
      });
    } catch {
      // autosave failed silently
    }
  }

  async function handleSubmit() {
    if (!confirm("Sınavı tamamlamak istediğinize emin misiniz?")) return;
    setSubmitting(true);
    try {
      await api.post(`/sessions/${sessionId}/submit`);
      router.push(`/exam/${sessionId}/result`);
    } catch {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Sınav yükleniyor...
      </div>
    );
  }

  if (!session || questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Sınav bulunamadı.
      </div>
    );
  }

  const question = questions[currentIndex];
  const currentAnswer = answers[question.id];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <span className="text-sm text-gray-600">
            Soru {currentIndex + 1} / {questions.length}
          </span>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded-md bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {submitting ? "Gönderiliyor..." : "Sınavı Bitir"}
          </button>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="rounded-lg bg-white border border-gray-200 p-6">
          <p className="text-lg text-gray-900 whitespace-pre-wrap">
            {question.stem}
          </p>

          <div className="mt-6">
            {question.question_type === "mcq" && question.options && (
              <div className="space-y-2">
                {question.options.map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() =>
                      saveAnswer(question.id, { key: opt.key })
                    }
                    className={`w-full text-left rounded-md border px-4 py-3 text-sm transition-colors ${
                      (currentAnswer as { key?: string })?.key === opt.key
                        ? "border-blue-500 bg-blue-50 text-blue-900"
                        : "border-gray-200 hover:bg-gray-50"
                    }`}
                  >
                    <span className="font-medium">{opt.key})</span> {opt.text}
                  </button>
                ))}
              </div>
            )}

            {question.question_type === "true_false" && (
              <div className="flex gap-4">
                {[true, false].map((val) => (
                  <button
                    key={String(val)}
                    onClick={() =>
                      saveAnswer(question.id, { value: val })
                    }
                    className={`flex-1 rounded-md border px-4 py-3 text-sm font-medium transition-colors ${
                      (currentAnswer as { value?: boolean })?.value === val
                        ? "border-blue-500 bg-blue-50 text-blue-900"
                        : "border-gray-200 hover:bg-gray-50"
                    }`}
                  >
                    {val ? "Doğru" : "Yanlış"}
                  </button>
                ))}
              </div>
            )}

            {question.question_type === "numeric" && (
              <input
                type="number"
                step="any"
                placeholder="Cevabınızı girin"
                defaultValue={
                  (currentAnswer as { value?: number })?.value ?? ""
                }
                onBlur={(e) =>
                  saveAnswer(question.id, {
                    value: parseFloat(e.target.value),
                  })
                }
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            )}

            {(question.question_type === "short_answer" ||
              question.question_type === "long_form") && (
              <textarea
                rows={question.question_type === "long_form" ? 8 : 3}
                placeholder="Cevabınızı yazın"
                defaultValue={
                  (currentAnswer as { text?: string })?.text ?? ""
                }
                onBlur={(e) =>
                  saveAnswer(question.id, { text: e.target.value })
                }
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            )}
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
            disabled={currentIndex === 0}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Önceki
          </button>
          <div className="flex gap-1">
            {questions.map((q, i) => (
              <button
                key={q.id}
                onClick={() => setCurrentIndex(i)}
                className={`h-8 w-8 rounded text-xs font-medium ${
                  i === currentIndex
                    ? "bg-blue-600 text-white"
                    : answers[q.id]
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-600"
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
          <button
            onClick={() =>
              setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))
            }
            disabled={currentIndex === questions.length - 1}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Sonraki
          </button>
        </div>
      </div>
    </div>
  );
}
