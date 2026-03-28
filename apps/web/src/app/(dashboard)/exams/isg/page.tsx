"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type {
  ISGBlueprint,
  ISGTopicWeight,
  ISGRubric,
  ISGExamResult,
  ISGGenerateTaskResult,
  ISGTaskStatus,
  ISGTaskProgressTopic,
} from "@/types";

type WizardStep = "class" | "config" | "generate" | "done";

export default function ISGWizardPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  const [step, setStep] = useState<WizardStep>("class");

  const [blueprints, setBluePrints] = useState<ISGBlueprint[]>([]);
  const [rubrics, setRubrics] = useState<ISGRubric[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedClass, setSelectedClass] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [shuffleQuestions, setShuffleQuestions] = useState(true);
  const [shuffleOptions, setShuffleOptions] = useState(true);
  const [topicOverrides, setTopicOverrides] = useState<Record<string, number>>({});

  const [questionTypes, setQuestionTypes] = useState<string[]>(["mcq"]);
  const [difficulty, setDifficulty] = useState<number>(3);
  const [useRag, setUseRag] = useState(false);
  const [selectedRubric, setSelectedRubric] = useState<string>("");

  const [examResult, setExamResult] = useState<ISGExamResult | null>(null);
  const [creating, setCreating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Task progress state
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<ISGTaskStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [bpData, rubricData] = await Promise.all([
          api.get<{ blueprints: ISGBlueprint[] }>("/isg/blueprints"),
          api.get<{ rubrics: ISGRubric[] }>("/isg/rubrics"),
        ]);
        setBluePrints(bpData.blueprints);
        setRubrics(rubricData.rubrics);
      } catch {
        // handled
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const selectedBlueprint = blueprints.find((bp) => bp.exam_class === selectedClass);

  function getTopicDistribution(): ISGTopicWeight[] {
    if (!selectedBlueprint) return [];
    return selectedBlueprint.topic_weights.map((tw) => ({
      ...tw,
      question_count: topicOverrides[tw.topic_id] ?? tw.question_count,
    }));
  }

  function getTotalQuestions(): number {
    return getTopicDistribution().reduce((sum, tw) => sum + tw.question_count, 0);
  }

  async function handleCreateExam() {
    if (!selectedClass) return;
    setCreating(true);
    setError(null);
    try {
      const overrides = Object.entries(topicOverrides).map(
        ([topic_id, question_count]) => ({ topic_id, question_count })
      );
      const result = await api.post<ISGExamResult>("/isg/exams", {
        exam_class: selectedClass,
        title: title || undefined,
        shuffle_questions: shuffleQuestions,
        shuffle_options: shuffleOptions,
        topic_overrides: overrides.length > 0 ? overrides : undefined,
      });
      setExamResult(result);
      setStep("generate");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sınav oluşturulamadı");
    } finally {
      setCreating(false);
    }
  }

  const pollTaskStatus = useCallback(
    async (id: string) => {
      try {
        const status = await api.get<ISGTaskStatus>(`/isg/tasks/${id}`);
        setTaskStatus(status);

        if (status.status === "completed" || status.status === "failed") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setGenerating(false);

          if (status.status === "completed") {
            setStep("done");
          } else {
            setError(status.error || "Soru üretimi başarısız oldu");
          }
        }
      } catch {
        // Keep polling on transient errors
      }
    },
    []
  );

  async function handleGenerate() {
    if (!examResult) return;
    setGenerating(true);
    setError(null);
    setTaskStatus(null);

    try {
      const result = await api.post<ISGGenerateTaskResult>(
        `/isg/exams/${examResult.template_id}/generate`,
        {
          template_id: examResult.template_id,
          question_types: questionTypes,
          difficulty,
          use_rag: useRag,
          rubric_id: selectedRubric || undefined,
        }
      );

      setTaskId(result.task_id);

      // Start polling every 1.5 seconds
      pollRef.current = setInterval(() => {
        pollTaskStatus(result.task_id);
      }, 1500);

      // First poll immediately
      pollTaskStatus(result.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Soru üretimi başlatılamadı");
      setGenerating(false);
    }
  }

  function toggleQuestionType(qt: string) {
    setQuestionTypes((prev) =>
      prev.includes(qt) ? prev.filter((t) => t !== qt) : [...prev, qt]
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12" style={{ color: "var(--text-secondary)" }}>
        Yükleniyor...
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/exams"
          style={{ color: "var(--link)", textDecoration: "none", fontSize: "0.875rem" }}
          onMouseEnter={(e) => { e.currentTarget.style.textDecoration = "underline"; }}
          onMouseLeave={(e) => { e.currentTarget.style.textDecoration = "none"; }}
        >
          &larr; Sınavlara Dön
        </Link>
        <h1
          className="mt-2 text-2xl font-bold"
          style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
        >
          ISG Sınav Oluşturma
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          OSHM müfredatına uygun ISG sınavı oluşturun
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-2 text-sm">
        {(["class", "config", "generate", "done"] as WizardStep[]).map((s, i) => {
          const labels = ["Sınıf Seçimi", "Yapılandırma", "Soru Üretimi", "Tamamlandı"];
          const isActive = step === s;
          const stepIndex = ["class", "config", "generate", "done"].indexOf(step);
          const isPast = i < stepIndex;
          return (
            <div key={s} className="flex items-center gap-2">
              {i > 0 && (
                <div
                  style={{
                    height: "1px",
                    width: "32px",
                    backgroundColor: isPast ? "var(--accent)" : "var(--border)",
                    transition: "background-color 0.2s",
                  }}
                />
              )}
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  borderRadius: "9999px",
                  paddingLeft: "0.75rem",
                  paddingRight: "0.75rem",
                  paddingTop: "0.25rem",
                  paddingBottom: "0.25rem",
                  fontSize: "0.75rem",
                  fontWeight: "500",
                  backgroundColor: isActive
                    ? "var(--accent)"
                    : isPast
                      ? "var(--accent-light)"
                      : "var(--card)",
                  color: isActive
                    ? "white"
                    : isPast
                      ? "var(--accent)"
                      : "var(--text-secondary)",
                  transition: "all 0.2s",
                }}
              >
                {labels[i]}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <div
          className="rounded-md border p-3 text-sm"
          style={{
            backgroundColor: "var(--danger-light)",
            borderColor: "var(--danger)",
            color: "var(--danger)",
          }}
        >
          {error}
        </div>
      )}

      {/* Step 1: Class Selection */}
      {step === "class" && (
        <div className="space-y-4">
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
          >
            ISG Sınıf Seçimi
          </h2>
          <div className="grid gap-4">
            {blueprints.map((bp) => (
              <button
                key={bp.exam_class}
                onClick={() => {
                  setSelectedClass(bp.exam_class);
                  setTitle(bp.title);
                  setTopicOverrides({});
                  setStep("config");
                }}
                style={{
                  textAlign: "left",
                  borderRadius: "0.5rem",
                  border: "2px solid var(--card)",
                  backgroundColor: "var(--card)",
                  padding: "1.25rem",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--card)"; }}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                      {bp.exam_class} Sınıfı
                    </h3>
                    <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                      {bp.description}
                    </p>
                    <div className="mt-3 flex items-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
                      <span>{bp.total_questions} soru</span>
                      <span>{bp.time_limit_minutes} dakika</span>
                      <span>Geçme: %{bp.pass_score}</span>
                    </div>
                  </div>
                  <span
                    style={{
                      display: "inline-flex",
                      height: "40px",
                      width: "40px",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: "9999px",
                      backgroundColor: "var(--accent-light)",
                      color: "var(--accent)",
                      fontSize: "1.125rem",
                      fontWeight: "bold",
                    }}
                  >
                    {bp.exam_class}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Configuration */}
      {step === "config" && selectedBlueprint && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2
              className="text-lg font-semibold"
              style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
            >
              {selectedBlueprint.exam_class} Sınıfı Yapılandırma
            </h2>
            <button
              onClick={() => setStep("class")}
              className="text-sm"
              style={{
                color: "var(--text-secondary)",
                backgroundColor: "transparent",
                border: "none",
                cursor: "pointer",
                transition: "color 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-primary)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-secondary)"; }}
            >
              Sınıf Değiştir
            </button>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Sınav Başlığı
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                marginTop: "0.25rem",
                display: "block",
                width: "100%",
                borderRadius: "0.375rem",
                backgroundColor: "var(--background)",
                borderColor: "var(--input-border)",
                borderWidth: "1px",
                padding: "0.5rem 0.75rem",
                fontSize: "0.875rem",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--input-focus)";
                e.currentTarget.style.outline = "none";
                e.currentTarget.style.boxShadow = "0 0 0 1px var(--input-focus)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--input-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Shuffle options */}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm" style={{ color: "var(--text-primary)" }}>
              <input
                type="checkbox"
                checked={shuffleQuestions}
                onChange={(e) => setShuffleQuestions(e.target.checked)}
                style={{ borderRadius: "0.25rem", borderColor: "var(--input-border)", accentColor: "var(--accent)" }}
              />
              Soruları Karıştır
            </label>
            <label className="flex items-center gap-2 text-sm" style={{ color: "var(--text-primary)" }}>
              <input
                type="checkbox"
                checked={shuffleOptions}
                onChange={(e) => setShuffleOptions(e.target.checked)}
                style={{ borderRadius: "0.25rem", borderColor: "var(--input-border)", accentColor: "var(--accent)" }}
              />
              Seçenekleri Karıştır
            </label>
          </div>

          {/* Topic Distribution */}
          <div>
            <h3 className="text-sm font-medium mb-3" style={{ color: "var(--text-primary)" }}>
              Konu Dağılımı
              <span className="ml-2 font-normal" style={{ color: "var(--text-muted)" }}>
                (Toplam: {getTotalQuestions()} soru)
              </span>
            </h3>
            <div className="space-y-2">
              {selectedBlueprint.topic_weights.map((tw) => {
                const current = topicOverrides[tw.topic_id] ?? tw.question_count;
                return (
                  <div
                    key={tw.topic_id}
                    className="flex items-center gap-3 rounded-md p-3"
                    style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                        {tw.topic_name}
                      </p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        Ağırlık: %{Math.round(tw.weight * 100)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          setTopicOverrides((prev) => ({
                            ...prev,
                            [tw.topic_id]: Math.max(0, current - 1),
                          }))
                        }
                        style={{
                          height: "28px", width: "28px", borderRadius: "0.25rem",
                          border: "1px solid var(--border)", backgroundColor: "transparent",
                          color: "var(--text-secondary)", fontSize: "0.875rem", cursor: "pointer",
                          transition: "all 0.2s",
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--card-hover)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
                      >
                        -
                      </button>
                      <span className="w-8 text-center text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {current}
                      </span>
                      <button
                        onClick={() =>
                          setTopicOverrides((prev) => ({
                            ...prev,
                            [tw.topic_id]: current + 1,
                          }))
                        }
                        style={{
                          height: "28px", width: "28px", borderRadius: "0.25rem",
                          border: "1px solid var(--border)", backgroundColor: "transparent",
                          color: "var(--text-secondary)", fontSize: "0.875rem", cursor: "pointer",
                          transition: "all 0.2s",
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--card-hover)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
                      >
                        +
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3">
            <button
              onClick={() => setStep("class")}
              style={{
                borderRadius: "0.375rem", border: "1px solid var(--border)",
                backgroundColor: "transparent", color: "var(--text-primary)",
                padding: "0.5rem 1rem", fontSize: "0.875rem", cursor: "pointer", transition: "all 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--card-hover)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
            >
              Geri
            </button>
            <button
              onClick={handleCreateExam}
              disabled={creating}
              style={{
                borderRadius: "0.375rem", backgroundColor: "var(--accent)",
                color: "white", padding: "0.5rem 1rem", fontSize: "0.875rem",
                fontWeight: "500", border: "none",
                cursor: creating ? "not-allowed" : "pointer",
                opacity: creating ? 0.5 : 1, transition: "background-color 0.2s",
              }}
              onMouseEnter={(e) => { if (!creating) e.currentTarget.style.backgroundColor = "var(--accent-hover)"; }}
              onMouseLeave={(e) => { if (!creating) e.currentTarget.style.backgroundColor = "var(--accent)"; }}
            >
              {creating ? "Oluşturuluyor..." : "Sınavı Oluştur"}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Generate Questions */}
      {step === "generate" && examResult && (
        <div className="space-y-6">
          <div
            className="rounded-lg border p-4"
            style={{ border: "1px solid var(--success)", backgroundColor: "var(--success-light)" }}
          >
            <p className="text-sm font-medium" style={{ color: "var(--success)" }}>
              Sınav şablonu oluşturuldu!
            </p>
            <p className="mt-1 text-xs" style={{ color: "var(--success)" }}>
              {examResult.title} - {examResult.total_questions} soru planlandı
            </p>
          </div>

          {/* Show progress if generating */}
          {generating && taskStatus ? (
            <div className="space-y-4">
              <h2
                className="text-lg font-semibold"
                style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
              >
                Sorular Üretiliyor...
              </h2>

              {/* Overall progress bar */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span style={{ color: "var(--text-secondary)" }}>Toplam İlerleme</span>
                  <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>
                    {taskStatus.total_generated} / {taskStatus.total_requested} soru
                  </span>
                </div>
                <div
                  style={{
                    height: "8px",
                    borderRadius: "4px",
                    backgroundColor: "var(--border)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      borderRadius: "4px",
                      backgroundColor: "var(--accent)",
                      width: taskStatus.total_requested > 0
                        ? `${(taskStatus.total_generated / taskStatus.total_requested) * 100}%`
                        : "0%",
                      transition: "width 0.5s ease",
                    }}
                  />
                </div>
              </div>

              {/* Per-topic progress */}
              <div className="space-y-2">
                {taskStatus.topic_progress.map((tp) => (
                  <div
                    key={tp.topic_id}
                    className="rounded-md p-3"
                    style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span
                          style={{
                            display: "inline-block",
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            backgroundColor:
                              tp.status === "done"
                                ? "var(--success)"
                                : tp.status === "generating"
                                  ? "var(--accent)"
                                  : tp.status === "error"
                                    ? "var(--danger)"
                                    : "var(--border)",
                            animation: tp.status === "generating" ? "pulse 1.5s infinite" : "none",
                          }}
                        />
                        <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                          {tp.topic_name}
                        </span>
                      </div>
                      <span
                        className="text-xs font-medium"
                        style={{
                          color:
                            tp.status === "done"
                              ? "var(--success)"
                              : tp.status === "generating"
                                ? "var(--accent)"
                                : tp.status === "error"
                                  ? "var(--danger)"
                                  : "var(--text-muted)",
                        }}
                      >
                        {tp.status === "pending" && "Bekliyor"}
                        {tp.status === "generating" && "Üretiliyor..."}
                        {tp.status === "done" && `${tp.generated_count}/${tp.requested_count}`}
                        {tp.status === "error" && "Hata"}
                      </span>
                    </div>
                    {(tp.status === "generating" || tp.status === "done") && (
                      <div
                        style={{
                          height: "4px",
                          borderRadius: "2px",
                          backgroundColor: "var(--border)",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            borderRadius: "2px",
                            backgroundColor:
                              tp.status === "done" ? "var(--success)" : "var(--accent)",
                            width: tp.requested_count > 0
                              ? `${(tp.generated_count / tp.requested_count) * 100}%`
                              : "0%",
                            transition: "width 0.5s ease",
                          }}
                        />
                      </div>
                    )}
                    {tp.errors.length > 0 && (
                      <p className="text-xs mt-1" style={{ color: "var(--danger)" }}>
                        {tp.errors[0]}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Pulse animation */}
              <style>{`
                @keyframes pulse {
                  0%, 100% { opacity: 1; }
                  50% { opacity: 0.4; }
                }
              `}</style>
            </div>
          ) : !generating ? (
            <>
              <h2
                className="text-lg font-semibold"
                style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
              >
                Soru Üretimi Ayarları
              </h2>

              {/* Question Types */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                  Soru Türleri
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: "mcq", label: "Çoktan Seçmeli" },
                    { value: "true_false", label: "Doğru/Yanlış" },
                    { value: "short_answer", label: "Kısa Cevap" },
                    { value: "long_form", label: "Uzun Cevap" },
                  ].map((qt) => (
                    <button
                      key={qt.value}
                      onClick={() => toggleQuestionType(qt.value)}
                      style={{
                        borderRadius: "9999px",
                        padding: "0.375rem 0.75rem",
                        fontSize: "0.75rem",
                        fontWeight: "500",
                        border: "1px solid",
                        backgroundColor: questionTypes.includes(qt.value) ? "var(--accent)" : "transparent",
                        color: questionTypes.includes(qt.value) ? "white" : "var(--text-primary)",
                        borderColor: questionTypes.includes(qt.value) ? "var(--accent)" : "var(--border)",
                        cursor: "pointer",
                        transition: "all 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        if (!questionTypes.includes(qt.value)) e.currentTarget.style.borderColor = "var(--accent)";
                      }}
                      onMouseLeave={(e) => {
                        if (!questionTypes.includes(qt.value)) e.currentTarget.style.borderColor = "var(--border)";
                      }}
                    >
                      {qt.label}
                    </button>
                  ))}
                </div>
                {questionTypes.length === 0 && (
                  <p className="mt-1 text-xs" style={{ color: "var(--danger)" }}>En az bir soru türü seçin</p>
                )}
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                  Zorluk Seviyesi: {difficulty}
                </label>
                <input
                  type="range" min={1} max={5} value={difficulty}
                  onChange={(e) => setDifficulty(Number(e.target.value))}
                  className="w-full" style={{ accentColor: "var(--accent)" }}
                />
                <div className="flex justify-between text-xs" style={{ color: "var(--text-muted)" }}>
                  <span>Kolay</span><span>Orta</span><span>Zor</span>
                </div>
              </div>

              {/* RAG toggle */}
              <label className="flex items-center gap-2 text-sm" style={{ color: "var(--text-primary)" }}>
                <input
                  type="checkbox" checked={useRag}
                  onChange={(e) => setUseRag(e.target.checked)}
                  style={{ borderRadius: "0.25rem", borderColor: "var(--input-border)", accentColor: "var(--accent)" }}
                />
                Yüklenen dokümanları kullan (RAG)
              </label>

              {/* Rubric selection for long_form */}
              {questionTypes.includes("long_form") && rubrics.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>
                    Varsayılan Rubrik (Uzun Cevap)
                  </label>
                  <select
                    value={selectedRubric}
                    onChange={(e) => setSelectedRubric(e.target.value)}
                    style={{
                      display: "block", width: "100%", borderRadius: "0.375rem",
                      backgroundColor: "var(--background)", borderColor: "var(--input-border)",
                      borderWidth: "1px", padding: "0.5rem 0.75rem", fontSize: "0.875rem",
                      color: "var(--text-primary)",
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "var(--input-focus)";
                      e.currentTarget.style.outline = "none";
                      e.currentTarget.style.boxShadow = "0 0 0 1px var(--input-focus)";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "var(--input-border)";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    <option value="">Otomatik (konuya göre)</option>
                    {rubrics.map((r) => (
                      <option key={r.rubric_id} value={r.rubric_id}>
                        {r.name} (Maks: {r.max_score} puan)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Topic summary */}
              <div
                className="rounded-lg p-4"
                style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
              >
                <h3 className="text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>
                  Konu Dağılımı Özeti
                </h3>
                <div className="space-y-1">
                  {examResult.topic_distribution.map((tw) => (
                    <div key={tw.topic_id} className="flex items-center justify-between text-xs">
                      <span style={{ color: "var(--text-secondary)" }}>{tw.topic_name}</span>
                      <span style={{ fontWeight: "500", color: "var(--text-primary)" }}>
                        {tw.question_count} soru
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => router.push(`/exams/${examResult.template_id}`)}
                  style={{
                    borderRadius: "0.375rem", border: "1px solid var(--border)",
                    backgroundColor: "transparent", color: "var(--text-primary)",
                    padding: "0.5rem 1rem", fontSize: "0.875rem", cursor: "pointer", transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--card-hover)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
                >
                  Atla ve Şablona Git
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={generating || questionTypes.length === 0}
                  style={{
                    borderRadius: "0.375rem", backgroundColor: "var(--accent)",
                    color: "white", padding: "0.5rem 1rem", fontSize: "0.875rem",
                    fontWeight: "500", border: "none",
                    cursor: generating || questionTypes.length === 0 ? "not-allowed" : "pointer",
                    opacity: generating || questionTypes.length === 0 ? 0.5 : 1,
                    transition: "background-color 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    if (!generating && questionTypes.length > 0)
                      e.currentTarget.style.backgroundColor = "var(--accent-hover)";
                  }}
                  onMouseLeave={(e) => {
                    if (!generating && questionTypes.length > 0)
                      e.currentTarget.style.backgroundColor = "var(--accent)";
                  }}
                >
                  Soruları Üret
                </button>
              </div>
            </>
          ) : (
            /* Generating but no status yet */
            <div className="flex items-center justify-center py-8 gap-3">
              <div
                style={{
                  width: "20px", height: "20px", border: "2px solid var(--border)",
                  borderTopColor: "var(--accent)", borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              <span style={{ color: "var(--text-secondary)" }}>Görev başlatılıyor...</span>
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
          )}
        </div>
      )}

      {/* Step 4: Done */}
      {step === "done" && taskStatus && examResult && (
        <div className="space-y-6">
          <div
            className="rounded-lg border p-4"
            style={{ border: "1px solid var(--success)", backgroundColor: "var(--success-light)" }}
          >
            <p className="text-sm font-medium" style={{ color: "var(--success)" }}>
              Soru üretimi tamamlandı!
            </p>
            <p className="mt-1 text-xs" style={{ color: "var(--success)" }}>
              {taskStatus.total_generated} / {taskStatus.total_requested} soru üretildi
            </p>
          </div>

          {/* Per-topic results */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Konu Bazlı Sonuçlar
            </h3>
            {taskStatus.topic_progress.map((tr) => (
              <div
                key={tr.topic_id}
                className="flex items-center justify-between rounded-md p-3"
                style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
              >
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {tr.topic_name}
                  </p>
                  {tr.errors.length > 0 && (
                    <p className="text-xs mt-0.5" style={{ color: "var(--danger)" }}>
                      {tr.errors.join(", ")}
                    </p>
                  )}
                </div>
                <span
                  className="text-sm font-medium"
                  style={{
                    color:
                      tr.generated_count === tr.requested_count
                        ? "var(--success)"
                        : tr.generated_count > 0
                          ? "var(--warning)"
                          : "var(--danger)",
                  }}
                >
                  {tr.generated_count}/{tr.requested_count}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-end gap-3">
            <Link
              href="/exams"
              style={{
                borderRadius: "0.375rem", border: "1px solid var(--border)",
                backgroundColor: "transparent", color: "var(--text-primary)",
                padding: "0.5rem 1rem", fontSize: "0.875rem", textDecoration: "none",
                display: "inline-block", cursor: "pointer", transition: "all 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--card-hover)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
            >
              Sınav Listesi
            </Link>
            <Link
              href={`/exams/${examResult.template_id}`}
              style={{
                borderRadius: "0.375rem", backgroundColor: "var(--accent)",
                color: "white", padding: "0.5rem 1rem", fontSize: "0.875rem",
                fontWeight: "500", textDecoration: "none", display: "inline-block",
                cursor: "pointer", transition: "background-color 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-hover)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--accent)"; }}
            >
              Sınavı Görüntüle
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
