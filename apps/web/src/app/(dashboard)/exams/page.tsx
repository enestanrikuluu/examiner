"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import type { ExamTemplate, ExamTemplateListResponse } from "@/types";

export default function ExamsPage() {
  const { user } = useAuthStore();
  const [templates, setTemplates] = useState<ExamTemplate[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<ExamTemplateListResponse>("/templates");
        setTemplates(data.items);
        setTotal(data.total);
      } catch {
        // handled by api-client
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const isInstructor =
    user?.role === "instructor" || user?.role === "admin";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sınavlar</h1>
          <p className="mt-1 text-sm text-gray-600">
            {total} sınav şablonu
          </p>
        </div>
        {isInstructor && (
          <Link
            href="/exams/new"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Yeni Sınav
          </Link>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Yükleniyor...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          Henüz sınav şablonu yok.
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map((t) => (
            <Link
              key={t.id}
              href={`/exams/${t.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-5 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{t.title}</h3>
                  {t.description && (
                    <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                      {t.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                    <span>{t.locale}</span>
                    {t.time_limit_minutes && (
                      <span>{t.time_limit_minutes} dk</span>
                    )}
                    {t.question_count !== null && (
                      <span>{t.question_count} soru</span>
                    )}
                    <span className="capitalize">{t.exam_mode}</span>
                  </div>
                </div>
                <span
                  className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                    t.is_published
                      ? "bg-green-100 text-green-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  {t.is_published ? "Yayında" : "Taslak"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
