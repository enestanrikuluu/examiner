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
      <h1 className="text-2xl font-bold text-gray-900">Yeni Sınav Oluştur</h1>
      <p className="mt-1 text-sm text-gray-600">
        Sınav şablonunu oluşturun, sonra sorular ekleyin.
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div>
          <label
            htmlFor="title"
            className="block text-sm font-medium text-gray-700"
          >
            Sınav Başlığı *
          </label>
          <input
            id="title"
            name="title"
            type="text"
            required
            maxLength={500}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700"
          >
            Açıklama
          </label>
          <textarea
            id="description"
            name="description"
            rows={3}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="locale"
              className="block text-sm font-medium text-gray-700"
            >
              Dil
            </label>
            <select
              id="locale"
              name="locale"
              defaultValue="tr-TR"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="tr-TR">Türkçe</option>
              <option value="en-US">English</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="exam_mode"
              className="block text-sm font-medium text-gray-700"
            >
              Sınav Modu
            </label>
            <select
              id="exam_mode"
              name="exam_mode"
              defaultValue="mock"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
              className="block text-sm font-medium text-gray-700"
            >
              Süre (dakika)
            </label>
            <input
              id="time_limit_minutes"
              name="time_limit_minutes"
              type="number"
              min={1}
              max={600}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="pass_score"
              className="block text-sm font-medium text-gray-700"
            >
              Geçme Notu (%)
            </label>
            <input
              id="pass_score"
              name="pass_score"
              type="number"
              min={0}
              max={100}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              name="shuffle_questions"
              className="rounded border-gray-300"
            />
            Soruları karıştır
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              name="shuffle_options"
              className="rounded border-gray-300"
            />
            Seçenekleri karıştır
          </label>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Oluşturuluyor..." : "Oluştur"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            İptal
          </button>
        </div>
      </form>
    </div>
  );
}
