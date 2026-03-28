"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useToastStore } from "@/components/Toast";
import type { ExamTemplate, ExamTemplateListResponse } from "@/types";

export default function ExamsPage() {
  const { user } = useAuthStore();
  const addToast = useToastStore((s) => s.add);
  const [templates, setTemplates] = useState<ExamTemplate[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [cardHoverId, setCardHoverId] = useState<string | null>(null);

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

  const handleDelete = async (e: React.MouseEvent, templateId: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (confirm("Bu sınav şablonunu silmek istediğinize emin misiniz?")) {
      try {
        await api.delete(`/templates/${templateId}`);
        setTemplates(templates.filter((t) => t.id !== templateId));
        addToast("Sınav şablonu silindi", "success");
      } catch {
        addToast("Silme işlemi başarısız", "error");
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}>Sınavlar</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            {total} sınav şablonu
          </p>
        </div>
        {isInstructor && (
          <div className="flex items-center gap-2">
            <Link
              href="/exams/isg"
              className="rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              style={{
                borderColor: "var(--input-border)",
                color: "var(--link)",
                backgroundColor: "transparent",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--accent-light)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              ISG Sınavı
            </Link>
            <Link
              href="/exams/new"
              className="rounded-md px-4 py-2 text-sm font-medium transition-colors"
              style={{
                backgroundColor: "var(--accent)",
                color: "#FFFAF5",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--accent-hover)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "var(--accent)";
              }}
            >
              Yeni Sınav
            </Link>
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>Yükleniyor...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>
          Henüz sınav şablonu yok.
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map((t) => (
            <Link
              key={t.id}
              href={`/exams/${t.id}`}
              className="block rounded-lg border p-5 transition-colors"
              style={{
                borderColor: cardHoverId === t.id ? "var(--accent)" : "var(--border-light)",
                backgroundColor: cardHoverId === t.id ? "var(--card-hover)" : "var(--card)",
              }}
              onMouseEnter={() => setCardHoverId(t.id)}
              onMouseLeave={() => setCardHoverId(null)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold" style={{ color: "var(--text-primary)" }}>{t.title}</h3>
                  {t.description && (
                    <p className="mt-1 text-sm line-clamp-2" style={{ color: "var(--text-secondary)" }}>
                      {t.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
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
                <div className="flex items-center gap-2">
                  <span
                    className="inline-flex rounded-full px-2 py-1 text-xs font-medium"
                    style={
                      t.is_published
                        ? {
                            backgroundColor: "var(--success-light)",
                            color: "var(--success)",
                          }
                        : {
                            backgroundColor: "var(--warning-light)",
                            color: "var(--warning)",
                          }
                    }
                  >
                    {t.is_published ? "Yayında" : "Taslak"}
                  </span>
                  {isInstructor && (
                    <button
                      onClick={(e) => handleDelete(e, t.id)}
                      className="p-1.5 rounded hover:opacity-70 transition-opacity"
                      style={{ color: "var(--danger)" }}
                      title="Sil"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        <line x1="10" y1="11" x2="10" y2="17" />
                        <line x1="14" y1="11" x2="14" y2="17" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
