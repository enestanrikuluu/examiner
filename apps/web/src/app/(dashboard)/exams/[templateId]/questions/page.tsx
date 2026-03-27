"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { QuestionItem } from "@/types";

const QUESTION_TYPES = [
  { value: "mcq", label: "Çoktan Seçmeli" },
  { value: "true_false", label: "Doğru/Yanlış" },
  { value: "numeric", label: "Sayısal" },
  { value: "short_answer", label: "Kısa Cevap" },
  { value: "long_form", label: "Uzun Cevap" },
];

export default function AddQuestionPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const router = useRouter();
  const [questionType, setQuestionType] = useState("mcq");
  const [stem, setStem] = useState("");
  const [options, setOptions] = useState([
    { key: "A", text: "" },
    { key: "B", text: "" },
    { key: "C", text: "" },
    { key: "D", text: "" },
  ]);
  const [correctKey, setCorrectKey] = useState("A");
  const [trueFalseAnswer, setTrueFalseAnswer] = useState(true);
  const [numericValue, setNumericValue] = useState("");
  const [numericTolerance, setNumericTolerance] = useState("0.01");
  const [keywords, setKeywords] = useState("");
  const [topic, setTopic] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function buildPayload() {
    const base: Record<string, unknown> = {
      question_type: questionType,
      stem,
      topic: topic || null,
      explanation: explanation || null,
    };

    switch (questionType) {
      case "mcq":
        base.options = options;
        base.correct_answer = { key: correctKey };
        break;
      case "true_false":
        base.correct_answer = { value: trueFalseAnswer };
        break;
      case "numeric":
        base.correct_answer = {
          value: parseFloat(numericValue),
          tolerance: parseFloat(numericTolerance),
        };
        break;
      case "short_answer":
        base.correct_answer = {
          keywords: keywords
            .split(",")
            .map((k) => k.trim())
            .filter(Boolean),
        };
        break;
      case "long_form":
        base.correct_answer = {};
        base.rubric = {
          max_score: 10,
          criteria: [
            { id: "c1", description: "İçerik doğruluğu", max_points: 5 },
            { id: "c2", description: "Açıklama kalitesi", max_points: 5 },
          ],
        };
        break;
    }

    return base;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.post<QuestionItem>(
        `/templates/${templateId}/questions`,
        buildPayload()
      );
      router.push(`/exams/${templateId}`);
    } catch {
      setError("Soru eklenirken bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1
        className="text-2xl font-bold"
        style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
      >
        Soru Ekle
      </h1>

      {error && (
        <div
          className="mt-4 rounded-md p-3 text-sm"
          style={{
            backgroundColor: "var(--danger-light)",
            color: "var(--danger)",
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div>
          <label
            className="block text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            Soru Tipi
          </label>
          <select
            value={questionType}
            onChange={(e) => setQuestionType(e.target.value)}
            className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
            style={{
              backgroundColor: "var(--card)",
              borderColor: "var(--input-border)",
              color: "var(--text-primary)",
              border: "1px solid var(--input-border)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--accent)";
              e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--input-border)";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            {QUESTION_TYPES.map((qt) => (
              <option key={qt.value} value={qt.value}>
                {qt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="block text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            Soru Metni *
          </label>
          <textarea
            value={stem}
            onChange={(e) => setStem(e.target.value)}
            required
            rows={3}
            className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
            style={{
              backgroundColor: "var(--card)",
              borderColor: "var(--input-border)",
              color: "var(--text-primary)",
              border: "1px solid var(--input-border)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--accent)";
              e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--input-border)";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
        </div>

        {/* MCQ options */}
        {questionType === "mcq" && (
          <div className="space-y-3">
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Seçenekler
            </label>
            {options.map((opt, i) => (
              <div key={opt.key} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="correct"
                  checked={correctKey === opt.key}
                  onChange={() => setCorrectKey(opt.key)}
                  className="h-4 w-4"
                  style={{ accentColor: "var(--accent)" }}
                />
                <span
                  className="text-sm font-medium w-6"
                  style={{ color: "var(--text-muted)" }}
                >
                  {opt.key})
                </span>
                <input
                  type="text"
                  value={opt.text}
                  onChange={(e) => {
                    const next = [...options];
                    next[i] = { ...opt, text: e.target.value };
                    setOptions(next);
                  }}
                  required
                  className="flex-1 rounded-md px-3 py-1.5 text-sm"
                  style={{
                    backgroundColor: "var(--card)",
                    borderColor: "var(--input-border)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--input-border)",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "var(--accent)";
                    e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "var(--input-border)";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                  placeholder={`Seçenek ${opt.key}`}
                />
              </div>
            ))}
            {options.length < 6 && (
              <button
                type="button"
                onClick={() => {
                  const nextKey = String.fromCharCode(65 + options.length);
                  setOptions([...options, { key: nextKey, text: "" }]);
                }}
                className="text-sm"
                style={{ color: "var(--accent)" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.color =
                    "var(--accent-hover)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.color = "var(--accent)";
                }}
              >
                + Seçenek Ekle
              </button>
            )}
          </div>
        )}

        {/* True/False */}
        {questionType === "true_false" && (
          <div>
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Doğru Cevap
            </label>
            <div className="mt-2 flex gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={trueFalseAnswer === true}
                  onChange={() => setTrueFalseAnswer(true)}
                  className="h-4 w-4"
                  style={{ accentColor: "var(--accent)" }}
                />
                <span style={{ color: "var(--text-primary)" }}>Doğru</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={trueFalseAnswer === false}
                  onChange={() => setTrueFalseAnswer(false)}
                  className="h-4 w-4"
                  style={{ accentColor: "var(--accent)" }}
                />
                <span style={{ color: "var(--text-primary)" }}>Yanlış</span>
              </label>
            </div>
          </div>
        )}

        {/* Numeric */}
        {questionType === "numeric" && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                Doğru Değer *
              </label>
              <input
                type="number"
                step="any"
                value={numericValue}
                onChange={(e) => setNumericValue(e.target.value)}
                required
                className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
                style={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--input-border)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--input-border)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
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
                style={{ color: "var(--text-secondary)" }}
              >
                Tolerans
              </label>
              <input
                type="number"
                step="any"
                value={numericTolerance}
                onChange={(e) => setNumericTolerance(e.target.value)}
                className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
                style={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--input-border)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--input-border)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "var(--input-border)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
          </div>
        )}

        {/* Short answer */}
        {questionType === "short_answer" && (
          <div>
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Anahtar Kelimeler (virgülle ayırın) *
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              required
              placeholder="Ankara, Türkiye"
              className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
              style={{
                backgroundColor: "var(--card)",
                borderColor: "var(--input-border)",
                color: "var(--text-primary)",
                border: "1px solid var(--input-border)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--input-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>
        )}

        {/* Long form - rubric note */}
        {questionType === "long_form" && (
          <div
            className="rounded-md p-3 text-sm"
            style={{
              backgroundColor: "var(--accent-light)",
              color: "var(--accent)",
            }}
          >
            Uzun cevaplı sorular için varsayılan rubrik uygulanır. Rubrik
            düzenleme Phase 4&apos;te eklenecektir.
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              className="block text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              Konu
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
              style={{
                backgroundColor: "var(--card)",
                borderColor: "var(--input-border)",
                color: "var(--text-primary)",
                border: "1px solid var(--input-border)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
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
              style={{ color: "var(--text-secondary)" }}
            >
              Açıklama
            </label>
            <input
              type="text"
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              className="mt-1 block w-full rounded-md px-3 py-2 text-sm"
              style={{
                backgroundColor: "var(--card)",
                borderColor: "var(--input-border)",
                color: "var(--text-primary)",
                border: "1px solid var(--input-border)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 0 0 1px var(--accent)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--input-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md px-4 py-2 text-sm font-medium text-white"
            style={{
              backgroundColor: "var(--accent)",
              opacity: loading ? 0.5 : 1,
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                (e.currentTarget as HTMLElement).style.backgroundColor =
                  "var(--accent-hover)";
              }
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor =
                "var(--accent)";
            }}
          >
            {loading ? "Ekleniyor..." : "Soru Ekle"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md px-4 py-2 text-sm font-medium"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              backgroundColor: "transparent",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor =
                "var(--card-hover)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor =
                "transparent";
            }}
          >
            İptal
          </button>
        </div>
      </form>
    </div>
  );
}
