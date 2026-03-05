"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import QuestionRenderer from "@/components/exam/QuestionRenderer";
import ThetaChart from "@/components/exam/ThetaChart";
import type {
  AdaptiveNextQuestion,
  AdaptiveNoMore,
  AdaptiveRespondResult,
  AdaptiveSession,
  ThetaHistoryEntry,
} from "@/types";

type NextResult = AdaptiveNextQuestion | AdaptiveNoMore;

function isFinished(result: NextResult): result is AdaptiveNoMore {
  return result.is_finished === true && !("question_id" in result);
}

export default function AdaptiveExamPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [session, setSession] = useState<AdaptiveSession | null>(null);
  const [currentQuestion, setCurrentQuestion] =
    useState<AdaptiveNextQuestion | null>(null);
  const [answer, setAnswer] = useState<Record<string, unknown> | undefined>(
    undefined
  );
  const [thetaHistory, setThetaHistory] = useState<ThetaHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finished, setFinished] = useState(false);
  const [finishReason, setFinishReason] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AdaptiveRespondResult | null>(
    null
  );

  const fetchNextQuestion = useCallback(async () => {
    try {
      const result = await api.get<NextResult>(
        `/adaptive/sessions/${sessionId}/next`
      );
      if (isFinished(result)) {
        setFinished(true);
        setFinishReason(result.finish_reason);
        setCurrentQuestion(null);
      } else {
        setCurrentQuestion(result);
        setAnswer(undefined);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Soru yuklenemedi"
      );
    }
  }, [sessionId]);

  // Initialize: create or resume
  useEffect(() => {
    setLoading(true);
    // The session was already created before navigating here.
    // Just fetch the first question.
    fetchNextQuestion().finally(() => setLoading(false));
  }, [fetchNextQuestion]);

  // Load theta history on mount
  useEffect(() => {
    api
      .get<{
        session_id: string;
        current_theta: number | null;
        current_se: number | null;
        history: ThetaHistoryEntry[];
      }>(`/adaptive/sessions/${sessionId}/theta`)
      .then((data) => {
        setThetaHistory(data.history);
        setSession({
          session_id: data.session_id,
          template_id: "",
          status: "in_progress",
          theta: data.current_theta,
          se: data.current_se,
          items_administered: data.history.length,
          max_items: 40,
        });
      })
      .catch(() => {
        // ignore
      });
  }, [sessionId]);

  async function handleSubmitAnswer() {
    if (!currentQuestion || !answer) return;

    setSubmitting(true);
    setLastResult(null);
    try {
      const result = await api.post<AdaptiveRespondResult>(
        `/adaptive/sessions/${sessionId}/respond`,
        {
          question_id: currentQuestion.question_id,
          answer,
        }
      );

      setLastResult(result);

      // Update theta history
      setThetaHistory((prev) => [
        ...prev,
        {
          step: result.step,
          question_id: currentQuestion.question_id,
          theta: result.theta,
          se: result.se,
          is_correct: result.is_correct,
          information: null,
        },
      ]);

      // Update session
      setSession((prev) =>
        prev
          ? {
              ...prev,
              theta: result.theta,
              se: result.se,
              items_administered: result.step,
            }
          : null
      );

      if (result.is_finished) {
        setFinished(true);
        setFinishReason(result.finish_reason);
        setCurrentQuestion(null);
      } else {
        // Small delay to show feedback, then load next
        setTimeout(() => {
          setLastResult(null);
          fetchNextQuestion();
        }, 1500);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Cevap gonderilemedi"
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Adaptif sinav hazirlaniyor...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => {
              setError(null);
              fetchNextQuestion();
            }}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (finished) {
    return (
      <div className="min-h-screen bg-gray-50 py-10">
        <div className="max-w-4xl mx-auto px-4">
          <div className="rounded-lg bg-white border border-gray-200 p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Sinav Tamamlandi
            </h2>
            <p className="text-gray-600 mb-6">
              {finishReason === "precision_reached"
                ? "Yeterli hassasiyet duzeyine ulasildi."
                : finishReason === "max_items_reached"
                  ? "Maksimum soru sayisina ulasildi."
                  : "Tum sorular cevaplandi."}
            </p>

            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="rounded-md bg-blue-50 p-4">
                <p className="text-sm text-blue-600 font-medium">
                  Yetenek (Theta)
                </p>
                <p className="text-2xl font-bold text-blue-900">
                  {session?.theta?.toFixed(2) ?? "-"}
                </p>
              </div>
              <div className="rounded-md bg-green-50 p-4">
                <p className="text-sm text-green-600 font-medium">
                  Standart Hata
                </p>
                <p className="text-2xl font-bold text-green-900">
                  {session?.se?.toFixed(3) ?? "-"}
                </p>
              </div>
              <div className="rounded-md bg-purple-50 p-4">
                <p className="text-sm text-purple-600 font-medium">
                  Cevaplanan Soru
                </p>
                <p className="text-2xl font-bold text-purple-900">
                  {session?.items_administered ?? 0}
                </p>
              </div>
            </div>

            {thetaHistory.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Yetenek Tahmini Seyri
                </h3>
                <ThetaChart history={thetaHistory} />
              </div>
            )}

            <button
              onClick={() => router.push("/exams")}
              className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Sinavlara Don
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Soru bulunamadi.
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 rounded-md bg-purple-100 px-3 py-1 text-sm font-medium text-purple-700">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5"
                />
              </svg>
              Adaptif
            </span>
            <span className="text-sm font-medium text-gray-600">
              Soru {currentQuestion.step}
            </span>
            {session && (
              <span className="text-xs text-gray-400">
                {"\u03B8"} = {session.theta?.toFixed(2) ?? "0.00"}
                {session.se != null && ` (SE: ${session.se.toFixed(3)})`}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {lastResult && (
              <span
                className={`text-sm font-medium ${
                  lastResult.is_correct ? "text-green-600" : "text-red-600"
                }`}
              >
                {lastResult.is_correct ? "Dogru!" : "Yanlis"}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Question Area */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <QuestionRenderer
          question={{
            id: currentQuestion.question_id,
            template_id: "",
            question_type: currentQuestion.question_type,
            stem: currentQuestion.stem,
            options: currentQuestion.options,
            correct_answer: {},
            rubric: null,
            explanation: null,
            difficulty: null,
            discrimination: null,
            topic: null,
            subtopic: null,
            tags: null,
            sort_order: 0,
            is_active: true,
            created_at: "",
            updated_at: "",
          }}
          answer={answer}
          onAnswer={(a) => setAnswer(a)}
          questionNumber={currentQuestion.step}
          copyPasteBlocked={false}
        />

        <div className="mt-6 flex items-center justify-between">
          <div />
          <button
            onClick={handleSubmitAnswer}
            disabled={submitting || !answer}
            className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Gonderiliyor..." : "Cevapla"}
          </button>
        </div>

        {/* Theta mini chart */}
        {thetaHistory.length > 1 && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Yetenek Tahmini
            </h3>
            <ThetaChart history={thetaHistory} height={150} />
          </div>
        )}
      </div>
    </div>
  );
}
