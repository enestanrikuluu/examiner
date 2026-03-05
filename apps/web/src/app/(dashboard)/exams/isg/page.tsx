"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type {
  ISGBlueprint,
  ISGTopicWeight,
  ISGRubric,
  ISGExamResult,
  ISGGenerateResult,
} from "@/types";

type WizardStep = "class" | "config" | "generate" | "done";

export default function ISGWizardPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  // Step state
  const [step, setStep] = useState<WizardStep>("class");

  // Blueprints
  const [blueprints, setBluePrints] = useState<ISGBlueprint[]>([]);
  const [rubrics, setRubrics] = useState<ISGRubric[]>([]);
  const [loading, setLoading] = useState(true);

  // Class selection
  const [selectedClass, setSelectedClass] = useState<string | null>(null);

  // Config
  const [title, setTitle] = useState("");
  const [shuffleQuestions, setShuffleQuestions] = useState(true);
  const [shuffleOptions, setShuffleOptions] = useState(true);
  const [topicOverrides, setTopicOverrides] = useState<
    Record<string, number>
  >({});

  // Generation
  const [questionTypes, setQuestionTypes] = useState<string[]>(["mcq"]);
  const [difficulty, setDifficulty] = useState<number>(3);
  const [useRag, setUseRag] = useState(false);
  const [selectedRubric, setSelectedRubric] = useState<string>("");

  // Results
  const [examResult, setExamResult] = useState<ISGExamResult | null>(null);
  const [generateResult, setGenerateResult] =
    useState<ISGGenerateResult | null>(null);
  const [creating, setCreating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const selectedBlueprint = blueprints.find(
    (bp) => bp.exam_class === selectedClass
  );

  function getTopicDistribution(): ISGTopicWeight[] {
    if (!selectedBlueprint) return [];
    return selectedBlueprint.topic_weights.map((tw) => ({
      ...tw,
      question_count:
        topicOverrides[tw.topic_id] ?? tw.question_count,
    }));
  }

  function getTotalQuestions(): number {
    return getTopicDistribution().reduce(
      (sum, tw) => sum + tw.question_count,
      0
    );
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

  async function handleGenerate() {
    if (!examResult) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await api.post<ISGGenerateResult>(
        `/isg/exams/${examResult.template_id}/generate`,
        {
          template_id: examResult.template_id,
          question_types: questionTypes,
          difficulty,
          use_rag: useRag,
          rubric_id: selectedRubric || undefined,
        }
      );
      setGenerateResult(result);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Soru üretimi başarısız");
    } finally {
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
      <div className="flex items-center justify-center py-12 text-gray-500">
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
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          &larr; Sınavlara Dön
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">
          ISG Sınav Oluşturma
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          OSHM müfredatına uygun ISG sınavı oluşturun
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-2 text-sm">
        {(["class", "config", "generate", "done"] as WizardStep[]).map(
          (s, i) => {
            const labels = ["Sınıf Seçimi", "Yapılandırma", "Soru Üretimi", "Tamamlandı"];
            const isActive = step === s;
            const stepIndex = ["class", "config", "generate", "done"].indexOf(step);
            const isPast = i < stepIndex;
            return (
              <div key={s} className="flex items-center gap-2">
                {i > 0 && (
                  <div className={`h-px w-8 ${isPast ? "bg-blue-600" : "bg-gray-300"}`} />
                )}
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : isPast
                        ? "bg-blue-100 text-blue-800"
                        : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {labels[i]}
                </span>
              </div>
            );
          }
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Class Selection */}
      {step === "class" && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
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
                className="text-left rounded-lg border-2 border-gray-200 bg-white p-5 hover:border-blue-400 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {bp.exam_class} Sınıfı
                    </h3>
                    <p className="mt-1 text-sm text-gray-600">
                      {bp.description}
                    </p>
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                      <span>{bp.total_questions} soru</span>
                      <span>{bp.time_limit_minutes} dakika</span>
                      <span>Geçme: %{bp.pass_score}</span>
                    </div>
                  </div>
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-lg font-bold">
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
            <h2 className="text-lg font-semibold text-gray-900">
              {selectedBlueprint.exam_class} Sınıfı Yapılandırma
            </h2>
            <button
              onClick={() => setStep("class")}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sınıf Değiştir
            </button>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Sınav Başlığı
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Shuffle options */}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={shuffleQuestions}
                onChange={(e) => setShuffleQuestions(e.target.checked)}
                className="rounded border-gray-300"
              />
              Soruları Karıştır
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={shuffleOptions}
                onChange={(e) => setShuffleOptions(e.target.checked)}
                className="rounded border-gray-300"
              />
              Seçenekleri Karıştır
            </label>
          </div>

          {/* Topic Distribution */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Konu Dağılımı
              <span className="ml-2 text-gray-400 font-normal">
                (Toplam: {getTotalQuestions()} soru)
              </span>
            </h3>
            <div className="space-y-2">
              {selectedBlueprint.topic_weights.map((tw) => {
                const current =
                  topicOverrides[tw.topic_id] ?? tw.question_count;
                return (
                  <div
                    key={tw.topic_id}
                    className="flex items-center gap-3 rounded-md border border-gray-200 bg-white p-3"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {tw.topic_name}
                      </p>
                      <p className="text-xs text-gray-500">
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
                        className="h-7 w-7 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 text-sm"
                      >
                        -
                      </button>
                      <span className="w-8 text-center text-sm font-medium">
                        {current}
                      </span>
                      <button
                        onClick={() =>
                          setTopicOverrides((prev) => ({
                            ...prev,
                            [tw.topic_id]: current + 1,
                          }))
                        }
                        className="h-7 w-7 rounded border border-gray-300 text-gray-600 hover:bg-gray-100 text-sm"
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
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Geri
            </button>
            <button
              onClick={handleCreateExam}
              disabled={creating}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? "Oluşturuluyor..." : "Sınavı Oluştur"}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Generate Questions */}
      {step === "generate" && examResult && (
        <div className="space-y-6">
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm font-medium text-green-800">
              Sınav şablonu oluşturuldu!
            </p>
            <p className="mt-1 text-xs text-green-700">
              {examResult.title} - {examResult.total_questions} soru planlandı
            </p>
          </div>

          <h2 className="text-lg font-semibold text-gray-900">
            Soru Üretimi Ayarları
          </h2>

          {/* Question Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
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
                  className={`rounded-full px-3 py-1.5 text-xs font-medium border transition-colors ${
                    questionTypes.includes(qt.value)
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {qt.label}
                </button>
              ))}
            </div>
            {questionTypes.length === 0 && (
              <p className="mt-1 text-xs text-red-500">
                En az bir soru türü seçin
              </p>
            )}
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Zorluk Seviyesi: {difficulty}
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={difficulty}
              onChange={(e) => setDifficulty(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Kolay</span>
              <span>Orta</span>
              <span>Zor</span>
            </div>
          </div>

          {/* RAG toggle */}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="rounded border-gray-300"
            />
            Yüklenen dokümanları kullan (RAG)
          </label>

          {/* Rubric selection for long_form */}
          {questionTypes.includes("long_form") && rubrics.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Varsayılan Rubrik (Uzun Cevap)
              </label>
              <select
                value={selectedRubric}
                onChange={(e) => setSelectedRubric(e.target.value)}
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Konu Dağılımı Özeti
            </h3>
            <div className="space-y-1">
              {examResult.topic_distribution.map((tw) => (
                <div
                  key={tw.topic_id}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="text-gray-600">{tw.topic_name}</span>
                  <span className="font-medium text-gray-900">
                    {tw.question_count} soru
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3">
            <button
              onClick={() =>
                router.push(`/exams/${examResult.template_id}`)
              }
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Atla ve Şablona Git
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating || questionTypes.length === 0}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {generating ? "Sorular Üretiliyor..." : "Soruları Üret"}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Done */}
      {step === "done" && generateResult && examResult && (
        <div className="space-y-6">
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm font-medium text-green-800">
              Soru üretimi tamamlandı!
            </p>
            <p className="mt-1 text-xs text-green-700">
              {generateResult.total_generated} / {generateResult.total_requested}{" "}
              soru üretildi
            </p>
          </div>

          {/* Per-topic results */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">
              Konu Bazlı Sonuçlar
            </h3>
            {generateResult.topic_results.map((tr) => (
              <div
                key={tr.topic_id}
                className="flex items-center justify-between rounded-md border border-gray-200 bg-white p-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {tr.topic_name}
                  </p>
                  {tr.errors.length > 0 && (
                    <p className="text-xs text-red-500 mt-0.5">
                      {tr.errors.join(", ")}
                    </p>
                  )}
                </div>
                <span
                  className={`text-sm font-medium ${
                    tr.generated_count === tr.requested_count
                      ? "text-green-600"
                      : tr.generated_count > 0
                        ? "text-amber-600"
                        : "text-red-600"
                  }`}
                >
                  {tr.generated_count}/{tr.requested_count}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-end gap-3">
            <Link
              href="/exams"
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Sınav Listesi
            </Link>
            <Link
              href={`/exams/${examResult.template_id}`}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Sınavı Görüntüle
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
