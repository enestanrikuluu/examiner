"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, uploadFile } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type {
  ExamTemplate,
  QuestionItem,
  QuestionItemListResponse,
  ExamSession,
  AdaptiveSession,
  DocumentInfo,
  GenerateResult,
  GeneratedQuestion,
} from "@/types";

// ─── Document Upload Section ─────────────────────────────────────────

function DocumentSection({ templateId }: { templateId: string }) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .get<DocumentInfo[]>(`/templates/${templateId}/documents`)
      .then(setDocuments)
      .catch(() => {});
  }, [templateId]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const doc = await uploadFile<DocumentInfo>(
        `/templates/${templateId}/documents`,
        file
      );
      setDocuments((prev) => [doc, ...prev]);
    } catch {
      // handled
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(docId: string) {
    try {
      await api.delete(`/documents/${docId}`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch {
      // handled
    }
  }

  const statusLabels: Record<string, { label: string; bgColor: string; textColor: string }> = {
    pending: { label: "Bekliyor", bgColor: "var(--warning-light)", textColor: "var(--warning)" },
    processing: { label: "İşleniyor", bgColor: "var(--accent-light)", textColor: "var(--accent)" },
    ready: { label: "Hazır", bgColor: "var(--success-light)", textColor: "var(--success)" },
    failed: { label: "Hata", bgColor: "var(--danger-light)", textColor: "var(--danger)" },
  };

  function formatFileSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2
          className="text-lg font-semibold"
          style={{
            fontFamily: "var(--font-playfair), Georgia, serif",
            color: "var(--text-primary)",
          }}
        >
          Kaynak Dokümanlar ({documents.length})
        </h2>
        <label
          className="cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
          style={{
            background: "var(--nav)",
            color: "var(--text-primary)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--border-light)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "var(--nav)";
          }}
        >
          {uploading ? "Yükleniyor..." : "Doküman Yükle"}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>

      {documents.length === 0 ? (
        <div
          className="rounded-lg border p-6 text-center text-sm"
          style={{
            borderStyle: "dashed",
            borderColor: "var(--border)",
            color: "var(--text-muted)",
          }}
        >
          Henüz doküman yüklenmemiş. PDF, DOCX veya TXT dosyaları yükleyerek
          AI soru üretiminde kaynak materyal olarak kullanabilirsiniz.
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => {
            const status = statusLabels[doc.status] ?? {
              label: doc.status,
              bgColor: "var(--border-light)",
              textColor: "var(--text-secondary)",
            };
            return (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border px-4 py-3 transition-colors"
                style={{
                  borderColor: "var(--border)",
                  background: "var(--card)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--card-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--card)";
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="text-sm">
                    <span
                      className="font-medium"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {doc.filename}
                    </span>
                    <span
                      className="ml-2"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {formatFileSize(doc.file_size_bytes)}
                    </span>
                  </div>
                  <span
                    className="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                    style={{
                      background: status.bgColor,
                      color: status.textColor,
                    }}
                  >
                    {status.label}
                  </span>
                  {doc.status === "ready" && (
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {doc.chunk_count} parça
                    </span>
                  )}
                  {doc.error_message && (
                    <span
                      className="text-xs"
                      style={{ color: "var(--danger)" }}
                    >
                      {doc.error_message}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="text-xs transition-colors"
                  style={{ color: "var(--danger)" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--accent-hover)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--danger)";
                  }}
                >
                  Sil
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Generate Questions Modal ────────────────────────────────────────

function GenerateModal({
  templateId,
  locale,
  onGenerated,
  onClose,
  hasDocuments,
}: {
  templateId: string;
  locale: string;
  onGenerated: (questions: GeneratedQuestion[], errors: string[]) => void;
  onClose: () => void;
  hasDocuments: boolean;
}) {
  const [topic, setTopic] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [questionType, setQuestionType] = useState("mcq");
  const [count, setCount] = useState(5);
  const [difficulty, setDifficulty] = useState<number | "">("");
  const [useRag, setUseRag] = useState(hasDocuments);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) {
      setError("Konu alanı zorunludur.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await api.post<GenerateResult>("/ai/generate", {
        template_id: templateId,
        question_type: questionType,
        topic: topic.trim(),
        subtopic: subtopic.trim() || undefined,
        count,
        difficulty: difficulty || undefined,
        locale,
        use_rag: useRag,
      });
      onGenerated(result.questions, result.errors);
    } catch {
      setError("Soru üretimi sırasında bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  const typeOptions = [
    { value: "mcq", label: "Çoktan Seçmeli" },
    { value: "true_false", label: "Doğru/Yanlış" },
    { value: "numeric", label: "Sayısal" },
    { value: "short_answer", label: "Kısa Cevap" },
    { value: "long_form", label: "Uzun Cevap" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div
        className="w-full max-w-lg rounded-xl p-6 shadow-xl"
        style={{ background: "var(--card)" }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3
            className="text-lg font-semibold"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--text-primary)",
            }}
          >
            AI ile Soru Üret
          </h3>
          <button
            onClick={onClose}
            className="transition-colors"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-muted)";
            }}
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Konu *
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="ör. İş Sağlığı ve Güvenliği Mevzuatı"
              className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
              style={{
                background: "var(--background)",
                border: "1px solid var(--input-border)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-light)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--input-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          <div>
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Alt Konu
            </label>
            <input
              type="text"
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              placeholder="ör. Risk Değerlendirmesi"
              className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
              style={{
                background: "var(--background)",
                border: "1px solid var(--input-border)",
                color: "var(--text-primary)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-light)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--input-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                Soru Tipi
              </label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--input-border)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-light)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "var(--input-border)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                {typeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                className="block text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                Adet
              </label>
              <input
                type="number"
                value={count}
                onChange={(e) =>
                  setCount(Math.max(1, Math.min(50, +e.target.value)))
                }
                min={1}
                max={50}
                className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--input-border)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-light)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "var(--input-border)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                Zorluk (1-5)
              </label>
              <input
                type="number"
                value={difficulty}
                onChange={(e) =>
                  setDifficulty(e.target.value === "" ? "" : +e.target.value)
                }
                min={1}
                max={5}
                placeholder="Opsiyonel"
                className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--input-border)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-light)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "var(--input-border)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
            <div className="flex items-end">
              <label
                className="flex items-center gap-2 text-sm"
                style={{ color: "var(--text-primary)" }}
              >
                <input
                  type="checkbox"
                  checked={useRag}
                  onChange={(e) => setUseRag(e.target.checked)}
                  disabled={!hasDocuments}
                  className="h-4 w-4 rounded"
                  style={{
                    borderColor: "var(--input-border)",
                    accentColor: "var(--special)",
                  }}
                />
                Kaynak dokümanlardan yararlan
              </label>
            </div>
          </div>

          {error && (
            <p className="text-sm" style={{ color: "var(--danger)" }}>
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              style={{
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--border-light)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              Vazgeç
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors"
              style={{
                background: loading ? "var(--text-muted)" : "var(--special)",
                opacity: loading ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = "var(--special-light)";
                  e.currentTarget.style.color = "var(--special)";
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = "var(--special)";
                  e.currentTarget.style.color = "white";
                }
              }}
            >
              {loading ? "Üretiliyor..." : "Üret"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Review Generated Questions Panel ────────────────────────────────

function ReviewPanel({
  questions,
  errors,
  onAccept,
  onClose,
}: {
  questions: GeneratedQuestion[];
  errors: string[];
  onAccept: (indices: number[]) => void;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<Set<number>>(
    () => new Set(questions.map((_, i) => i))
  );

  function toggleSelect(idx: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  function selectAll() {
    setSelected(new Set(questions.map((_, i) => i)));
  }

  function deselectAll() {
    setSelected(new Set());
  }

  const questionTypeLabels: Record<string, string> = {
    mcq: "Çoktan Seçmeli",
    true_false: "Doğru/Yanlış",
    numeric: "Sayısal",
    short_answer: "Kısa Cevap",
    long_form: "Uzun Cevap",
  };

  return (
    <div
      className="space-y-4 rounded-xl border p-5"
      style={{
        borderColor: "var(--special-light)",
        background: "var(--special-light)",
      }}
    >
      <div className="flex items-center justify-between">
        <h3
          className="text-lg font-semibold"
          style={{
            fontFamily: "var(--font-playfair), Georgia, serif",
            color: "var(--text-primary)",
          }}
        >
          Üretilen Sorular ({questions.length})
        </h3>
        <button
          onClick={onClose}
          className="text-sm transition-colors"
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--text-secondary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--text-muted)";
          }}
        >
          Kapat
        </button>
      </div>

      {errors.length > 0 && (
        <div
          className="rounded-md p-3 text-sm"
          style={{
            background: "var(--danger-light)",
            color: "var(--danger)",
          }}
        >
          <p className="font-medium">Hatalar:</p>
          <ul className="mt-1 list-inside list-disc">
            {errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {questions.length > 0 && (
        <>
          <div className="flex items-center gap-3 text-sm">
            <button
              onClick={selectAll}
              className="transition-colors"
              style={{ color: "var(--link)" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--accent)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--link)";
              }}
            >
              Tümünü Seç
            </button>
            <button
              onClick={deselectAll}
              className="transition-colors"
              style={{ color: "var(--link)" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--accent)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--link)";
              }}
            >
              Seçimi Kaldır
            </button>
            <span style={{ color: "var(--text-muted)" }}>
              {selected.size} / {questions.length} seçili
            </span>
          </div>

          <div className="max-h-96 space-y-3 overflow-y-auto">
            {questions.map((q, i) => (
              <div
                key={i}
                className="rounded-lg border p-4 transition-colors"
                style={{
                  borderColor: selected.has(i)
                    ? "var(--special)"
                    : "var(--border)",
                  background: selected.has(i) ? "var(--card)" : "rgba(255,255,255,0.6)",
                  opacity: selected.has(i) ? 1 : 0.6,
                }}
                onMouseEnter={(e) => {
                  if (!selected.has(i)) {
                    e.currentTarget.style.opacity = "0.8";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selected.has(i)) {
                    e.currentTarget.style.opacity = "0.6";
                  }
                }}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={selected.has(i)}
                    onChange={() => toggleSelect(i)}
                    className="mt-1 h-4 w-4 rounded"
                    style={{
                      borderColor: "var(--input-border)",
                      accentColor: "var(--special)",
                    }}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span
                        className="rounded px-1.5 py-0.5"
                        style={{
                          background: "var(--border-light)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {questionTypeLabels[q.question_type] ?? q.question_type}
                      </span>
                      {q.topic && (
                        <span style={{ color: "var(--text-muted)" }}>
                          {q.topic}
                        </span>
                      )}
                      {q.difficulty != null && (
                        <span style={{ color: "var(--text-muted)" }}>
                          Zorluk: {q.difficulty}
                        </span>
                      )}
                    </div>
                    <p
                      className="mt-1 text-sm"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {q.stem}
                    </p>

                    {q.options && q.options.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {q.options.map((opt) => {
                          const isCorrect =
                            (q.correct_answer as Record<string, string>).key ===
                            opt.key;
                          return (
                            <li
                              key={opt.key}
                              className="text-sm"
                              style={{
                                color: isCorrect
                                  ? "var(--success)"
                                  : "var(--text-secondary)",
                                fontWeight: isCorrect ? "500" : "normal",
                              }}
                            >
                              {opt.key}) {opt.text}
                              {isCorrect && " ✓"}
                            </li>
                          );
                        })}
                      </ul>
                    )}

                    {q.explanation && (
                      <p
                        className="mt-2 text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        Açıklama: {q.explanation}
                      </p>
                    )}

                    {q.warnings.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {q.warnings.map((w, wi) => (
                          <p
                            key={wi}
                            className="text-xs"
                            style={{ color: "var(--warning)" }}
                          >
                            ⚠ {w}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              style={{
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--border-light)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              Vazgeç
            </button>
            <button
              onClick={() => onAccept(Array.from(selected))}
              disabled={selected.size === 0}
              className="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors"
              style={{
                background:
                  selected.size === 0
                    ? "var(--text-muted)"
                    : "var(--special)",
                opacity: selected.size === 0 ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (selected.size > 0) {
                  e.currentTarget.style.background = "var(--accent-hover)";
                }
              }}
              onMouseLeave={(e) => {
                if (selected.size > 0) {
                  e.currentTarget.style.background = "var(--special)";
                }
              }}
            >
              Seçilenleri Ekle ({selected.size})
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Main Template Detail Page ───────────────────────────────────────

export default function TemplateDetailPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const router = useRouter();
  const { user } = useAuthStore();
  const [template, setTemplate] = useState<ExamTemplate | null>(null);
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generatedQuestions, setGeneratedQuestions] = useState<
    GeneratedQuestion[]
  >([]);
  const [generationErrors, setGenerationErrors] = useState<string[]>([]);
  const [showReview, setShowReview] = useState(false);
  const [docCount, setDocCount] = useState(0);

  const isOwner =
    user?.role === "admin" ||
    (template && template.created_by === user?.id);

  useEffect(() => {
    async function load() {
      try {
        const [t, q, docs] = await Promise.all([
          api.get<ExamTemplate>(`/templates/${templateId}`),
          api.get<QuestionItemListResponse>(
            `/templates/${templateId}/questions`
          ),
          api
            .get<DocumentInfo[]>(`/templates/${templateId}/documents`)
            .catch(() => [] as DocumentInfo[]),
        ]);
        setTemplate(t);
        setQuestions(q.items);
        setDocCount(docs.filter((d) => d.status === "ready").length);
      } catch {
        // handled
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [templateId]);

  async function handlePublish() {
    if (!template) return;
    try {
      const updated = await api.post<ExamTemplate>(
        `/templates/${templateId}/publish`
      );
      setTemplate(updated);
    } catch {
      // handled
    }
  }

  async function handleDelete() {
    if (!confirm("Bu şablonu silmek istediğinize emin misiniz?")) return;
    try {
      await api.delete(`/templates/${templateId}`);
      router.push("/exams");
    } catch {
      // handled
    }
  }

  async function handleStartSession() {
    try {
      const session = await api.post<ExamSession>("/sessions", {
        template_id: templateId,
      });
      router.push(`/exam/${session.id}`);
    } catch {
      // handled
    }
  }

  async function handleStartAdaptive() {
    try {
      const adaptive = await api.post<AdaptiveSession>("/adaptive/sessions", {
        template_id: templateId,
      });
      router.push(`/exam/adaptive/${adaptive.session_id}`);
    } catch {
      // handled
    }
  }

  function handleGenerated(
    questions: GeneratedQuestion[],
    errors: string[]
  ) {
    setGeneratedQuestions(questions);
    setGenerationErrors(errors);
    setShowGenerateModal(false);
    setShowReview(true);
  }

  async function handleAcceptQuestions(indices: number[]) {
    const toAdd = indices.map((i) => generatedQuestions[i]);
    try {
      for (const q of toAdd) {
        await api.post(`/templates/${templateId}/questions`, {
          question_type: q.question_type,
          stem: q.stem,
          options: q.options,
          correct_answer: q.correct_answer,
          explanation: q.explanation,
          topic: q.topic,
          subtopic: q.subtopic,
          difficulty: q.difficulty,
        });
      }
      // Refresh questions list
      const updated = await api.get<QuestionItemListResponse>(
        `/templates/${templateId}/questions`
      );
      setQuestions(updated.items);
      setShowReview(false);
      setGeneratedQuestions([]);
      setGenerationErrors([]);
    } catch {
      // handled
    }
  }

  if (loading) {
    return (
      <div
        className="text-center py-12"
        style={{ color: "var(--text-muted)" }}
      >
        Yükleniyor...
      </div>
    );
  }

  if (!template) {
    return (
      <div
        className="text-center py-12"
        style={{ color: "var(--text-muted)" }}
      >
        Şablon bulunamadı.
      </div>
    );
  }

  const questionTypeLabels: Record<string, string> = {
    mcq: "Çoktan Seçmeli",
    true_false: "Doğru/Yanlış",
    numeric: "Sayısal",
    short_answer: "Kısa Cevap",
    long_form: "Uzun Cevap",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1
              className="text-2xl font-bold"
              style={{
                fontFamily: "var(--font-playfair), Georgia, serif",
                color: "var(--text-primary)",
              }}
            >
              {template.title}
            </h1>
            <span
              className="inline-flex rounded-full px-2 py-1 text-xs font-medium"
              style={{
                background: template.is_published
                  ? "var(--success-light)"
                  : "var(--warning-light)",
                color: template.is_published
                  ? "var(--success)"
                  : "var(--warning)",
              }}
            >
              {template.is_published ? "Yayında" : "Taslak"}
            </span>
          </div>
          {template.description && (
            <p
              className="mt-1 text-sm"
              style={{ color: "var(--text-secondary)" }}
            >
              {template.description}
            </p>
          )}
          <div
            className="mt-2 flex items-center gap-4 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            <span>{template.locale}</span>
            {template.time_limit_minutes && (
              <span>{template.time_limit_minutes} dk</span>
            )}
            {template.pass_score !== null && (
              <span>Geçme: %{template.pass_score}</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {template.is_published && (
            <>
              <button
                onClick={handleStartAdaptive}
                className="rounded-md border px-4 py-2 text-sm font-medium transition-colors"
                style={{
                  borderColor: "var(--special)",
                  color: "var(--special)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--special-light)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                Adaptif Sinav
              </button>
              <button
                onClick={handleStartSession}
                className="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors"
                style={{ background: "var(--success)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.opacity = "0.9";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.opacity = "1";
                }}
              >
                Sinava Basla
              </button>
            </>
          )}
          {isOwner && !template.is_published && (
            <button
              onClick={handlePublish}
              className="rounded-md px-4 py-2 text-sm font-medium text-white transition-colors"
              style={{ background: "var(--accent)" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--accent-hover)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "var(--accent)";
              }}
            >
              Yayınla
            </button>
          )}
          {isOwner && !template.is_published && (
            <button
              onClick={handleDelete}
              className="rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              style={{
                borderColor: "var(--danger)",
                color: "var(--danger)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--danger-light)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              Sil
            </button>
          )}
        </div>
      </div>

      {/* Document Upload Section (Owner only) */}
      {isOwner && <DocumentSection templateId={templateId} />}

      {/* Review generated questions */}
      {showReview && (
        <ReviewPanel
          questions={generatedQuestions}
          errors={generationErrors}
          onAccept={handleAcceptQuestions}
          onClose={() => {
            setShowReview(false);
            setGeneratedQuestions([]);
            setGenerationErrors([]);
          }}
        />
      )}

      {/* Questions section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2
            className="text-lg font-semibold"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--text-primary)",
            }}
          >
            Sorular ({questions.length})
          </h2>
          {isOwner && (
            <div className="flex gap-2">
              <button
                onClick={() => setShowGenerateModal(true)}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-white transition-colors"
                style={{ background: "var(--special)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--accent-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--special)";
                }}
              >
                AI ile Üret
              </button>
              <Link
                href={`/exams/${templateId}/questions`}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-white transition-colors"
                style={{ background: "var(--accent)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--accent-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--accent)";
                }}
              >
                Manuel Ekle
              </Link>
            </div>
          )}
        </div>

        {questions.length === 0 ? (
          <div
            className="rounded-lg border p-8 text-center text-sm"
            style={{
              borderStyle: "dashed",
              borderColor: "var(--border)",
              color: "var(--text-muted)",
            }}
          >
            Henüz soru eklenmemiş.
            {isOwner &&
              " Soru eklemek için yukarıdaki butonları kullanın."}
          </div>
        ) : (
          <div className="space-y-3">
            {questions.map((q, i) => (
              <div
                key={q.id}
                className="rounded-lg border p-4 transition-colors"
                style={{
                  borderColor: "var(--border)",
                  background: "var(--card)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--card-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--card)";
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-sm font-medium"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {i + 1}.
                      </span>
                      <span
                        className="inline-flex rounded px-1.5 py-0.5 text-xs"
                        style={{
                          background: "var(--border-light)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {questionTypeLabels[q.question_type] ?? q.question_type}
                      </span>
                      {q.topic && (
                        <span
                          className="text-xs"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {q.topic}
                        </span>
                      )}
                    </div>
                    <p
                      className="mt-1 text-sm"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {q.stem}
                    </p>
                  </div>
                  {!q.is_active && (
                    <span
                      className="rounded px-1.5 py-0.5 text-xs"
                      style={{
                        background: "var(--danger-light)",
                        color: "var(--danger)",
                      }}
                    >
                      Pasif
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Generate Questions Modal */}
      {showGenerateModal && (
        <GenerateModal
          templateId={templateId}
          locale={template.locale}
          onGenerated={handleGenerated}
          onClose={() => setShowGenerateModal(false)}
          hasDocuments={docCount > 0}
        />
      )}
    </div>
  );
}
