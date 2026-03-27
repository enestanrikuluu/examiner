"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { ExamTemplate } from "@/types";

export default function NewExamPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    const body = {
      title: form.get("title") as string,
      description: (form.get("description") as string) || null,
      locale: form.get("locale") as string,
      time_limit_minutes: form.get("time_limit_minutes")
        ? Number(form.get("time_limit_minutes"))
        : null,
      pass_score: form.get("pass_score")
        ? Number(form.get("pass_score"))
        : null,
      shuffle_questions: form.get("shuffle_questions") === "on",
      shuffle_options: form.get("shuffle_options") === "on",
      exam_mode: form.get("exam_mode") as string,
    };

    try {
      const template = await api.post<ExamTemplate>("/templates", body);
      router.push(`/exams/${template.id}`);
    } catch {
      setError("Sınav oluşturulurken bir hata oluştu.");
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
        Yeni Sınav Oluştur
      </h1>
      <p
        className="mt-1 text-sm"
        style={{ color: "var(--text-secondary)" }}
      >
        Sınav şablonunu oluşturun, sonra sorular ekleyin.
      </p>

      {error && (
        <div
          className="mt-4 rounded-md p-3 text-sm"
          style={{
            backgroundColor: "var(--danger-light)",
            color: "var(--danger)",
            borderLeft: "3px solid var(--danger)",
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div>
          <label
            htmlFor="title"
            className="block text-sm font-medium"
            style={{ color: "var(--text-primary)" }}
          >
            Sınav Başlığı *
          </label>
          <input
            id="title"
            name="title"
            type="text"
            required
            maxLength={500}
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

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium"
            style={{ color: "var(--text-primary)" }}
          >
            Açıklama
          </label>
          <textarea
            id="description"
            name="description"
            rows={3}
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
              fontFamily: "inherit",
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

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="locale"
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Dil
            </label>
            <select
              id="locale"
              name="locale"
              defaultValue="tr-TR"
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
            >
              <option value="tr-TR">Türkçe</option>
              <option value="en-US">English</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="exam_mode"
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Sınav Modu
            </label>
            <select
              id="exam_mode"
              name="exam_mode"
              defaultValue="mock"
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
            >
              <option value="practice">Alıştırma</option>
              <option value="mock">Deneme</option>
              <option value="high_stakes">Resmi Sınav</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="time_limit_minutes"
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Süre (dakika)
            </label>
            <input
              id="time_limit_minutes"
              name="time_limit_minutes"
              type="number"
              min={1}
              max={600}
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

          <div>
            <label
              htmlFor="pass_score"
              className="block text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Geçme Notu (%)
            </label>
            <input
              id="pass_score"
              name="pass_score"
              type="number"
              min={0}
              max={100}
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
        </div>

        <div className="flex items-center gap-6">
          <label
            className="flex items-center gap-2 text-sm"
            style={{ color: "var(--text-primary)" }}
          >
            <input
              type="checkbox"
              name="shuffle_questions"
              style={{
                borderRadius: "0.25rem",
                borderColor: "var(--input-border)",
                accentColor: "var(--accent)",
              }}
            />
            Soruları karıştır
          </label>
          <label
            className="flex items-center gap-2 text-sm"
            style={{ color: "var(--text-primary)" }}
          >
            <input
              type="checkbox"
              name="shuffle_options"
              style={{
                borderRadius: "0.25rem",
                borderColor: "var(--input-border)",
                accentColor: "var(--accent)",
              }}
            />
            Seçenekleri karıştır
          </label>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            style={{
              borderRadius: "0.375rem",
              backgroundColor: loading ? "var(--accent)" : "var(--accent)",
              color: "white",
              padding: "0.5rem 1rem",
              fontSize: "0.875rem",
              fontWeight: "500",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.5 : 1,
              transition: "background-color 0.2s",
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = "var(--accent-hover)";
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = "var(--accent)";
            }}
          >
            {loading ? "Oluşturuluyor..." : "Oluştur"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            style={{
              borderRadius: "0.375rem",
              backgroundColor: "transparent",
              color: "var(--text-primary)",
              padding: "0.5rem 1rem",
              fontSize: "0.875rem",
              fontWeight: "500",
              border: "1px solid var(--border)",
              cursor: "pointer",
              transition: "background-color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--card-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            İptal
          </button>
        </div>
      </form>
    </div>
  );
}
