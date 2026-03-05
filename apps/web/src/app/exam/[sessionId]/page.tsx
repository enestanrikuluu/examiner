"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";
import { useExamSessionStore } from "@/lib/stores/exam-session-store";
import IntegrityGuard from "@/components/exam/IntegrityGuard";
import QuestionRenderer from "@/components/exam/QuestionRenderer";
import Timer from "@/components/exam/Timer";

export default function ExamSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const {
    session,
    questions,
    answers,
    flags,
    currentIndex,
    loading,
    submitting,
    error,
    initialize,
    setCurrentIndex,
    saveAnswer,
    submitExam,
    heartbeat,
  } = useExamSessionStore();

  // Initialize session
  useEffect(() => {
    initialize(sessionId);
  }, [sessionId, initialize]);

  // Redirect if already submitted/graded
  useEffect(() => {
    if (
      session &&
      (session.status === "submitted" || session.status === "graded")
    ) {
      router.push(`/exam/${sessionId}/result`);
    }
  }, [session, sessionId, router]);

  // Periodic heartbeat (every 30s)
  useEffect(() => {
    if (session?.status !== "in_progress") return;

    heartbeatRef.current = setInterval(() => {
      heartbeat();
    }, 30_000);

    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, [session?.status, heartbeat]);

  const handleExpire = useCallback(async () => {
    // Auto-submit on timer expiry
    await submitExam();
    router.push(`/exam/${sessionId}/result`);
  }, [submitExam, sessionId, router]);

  async function handleSubmit() {
    if (!confirm("Sinavi tamamlamak istediginize emin misiniz?")) return;
    await submitExam();
    router.push(`/exam/${sessionId}/result`);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Sinav yukleniyor...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => initialize(sessionId)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!session || questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Sinav bulunamadi.
      </div>
    );
  }

  const question = questions[currentIndex];
  const currentAnswer = answers[question.id] as
    | Record<string, unknown>
    | undefined;
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Integrity Guard (invisible) */}
      {flags && (
        <IntegrityGuard
          tabSwitchDetection={flags.tab_switch_detection}
          copyPasteBlock={flags.copy_paste_block}
          fullscreenRequired={flags.fullscreen_required}
        />
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-600">
              Soru {currentIndex + 1} / {questions.length}
            </span>
            <span className="text-xs text-gray-400">
              {answeredCount} / {questions.length} cevaplandi
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Timer expiresAt={session.expires_at} onExpire={handleExpire} />
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="rounded-md bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {submitting ? "Gonderiliyor..." : "Sinavi Bitir"}
            </button>
          </div>
        </div>
      </div>

      {/* Question Area */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <QuestionRenderer
          question={question}
          answer={currentAnswer}
          onAnswer={(answer) => saveAnswer(question.id, answer)}
          questionNumber={currentIndex + 1}
          copyPasteBlocked={flags?.copy_paste_block ?? false}
        />

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Onceki
          </button>

          {/* Question Grid */}
          <div className="flex flex-wrap gap-1 justify-center max-w-lg">
            {questions.map((q, i) => {
              const isAnswered = !!answers[q.id];
              const isCurrent = i === currentIndex;
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentIndex(i)}
                  className={`h-8 w-8 rounded text-xs font-medium transition-colors ${
                    isCurrent
                      ? "bg-blue-600 text-white"
                      : isAnswered
                        ? "bg-green-100 text-green-800 hover:bg-green-200"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                  title={`Soru ${i + 1}${isAnswered ? " (cevaplandi)" : ""}`}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>

          <button
            onClick={() =>
              setCurrentIndex(Math.min(questions.length - 1, currentIndex + 1))
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
