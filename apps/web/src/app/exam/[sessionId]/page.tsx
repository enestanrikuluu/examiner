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
      <div className="min-h-screen flex items-center justify-center" style={{ color: "var(--text-secondary)" }}>
        Sinav yukleniyor...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--background)" }}>
        <div className="text-center">
          <p className="mb-4" style={{ color: "var(--danger)" }}>{error}</p>
          <button
            onClick={() => initialize(sessionId)}
            className="rounded-md px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            style={{ backgroundColor: "var(--accent)" }}
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!session || questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ color: "var(--text-secondary)", backgroundColor: "var(--background)" }}>
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
    <div className="min-h-screen" style={{ backgroundColor: "var(--background)" }}>
      {/* Integrity Guard (invisible) */}
      {flags && (
        <IntegrityGuard
          tabSwitchDetection={flags.tab_switch_detection}
          copyPasteBlock={flags.copy_paste_block}
          fullscreenRequired={flags.fullscreen_required}
        />
      )}

      {/* Header */}
      <div className="px-4 py-3 sticky top-0 z-10" style={{ backgroundColor: "var(--card)", borderBottom: "1px solid var(--border)" }}>
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Soru {currentIndex + 1} / {questions.length}
            </span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              {answeredCount} / {questions.length} cevaplandi
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Timer expiresAt={session.expires_at} onExpire={handleExpire} />
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="rounded-md px-4 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: "var(--danger)" }}
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
            className="rounded-md px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
            style={{
              border: "1px solid var(--border)",
              color: "var(--text-secondary)"
            }}
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
                  className="h-8 w-8 rounded text-xs font-medium transition-colors"
                  style={{
                    backgroundColor: isCurrent
                      ? "var(--accent)"
                      : isAnswered
                        ? "var(--success-light)"
                        : "var(--card-hover)",
                    color: isCurrent
                      ? "white"
                      : isAnswered
                        ? "var(--success)"
                        : "var(--text-secondary)",
                  }}
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
            className="rounded-md px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
            style={{
              border: "1px solid var(--border)",
              color: "var(--text-secondary)"
            }}
          >
            Sonraki
          </button>
        </div>
      </div>
    </div>
  );
}
