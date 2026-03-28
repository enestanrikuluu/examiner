"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useRouter } from "next/navigation";

interface SessionItem {
  id: string;
  template_id: string;
  user_id: string;
  status: string;
  started_at: string | null;
  submitted_at: string | null;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  passed: boolean | null;
  created_at: string;
}

interface UserInfo {
  id: string;
  full_name: string;
  email: string;
}

interface TemplateInfo {
  id: string;
  title: string;
  pass_score: number;
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AdminResultsPage() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [users, setUsers] = useState<Record<string, UserInfo>>({});
  const [templates, setTemplates] = useState<Record<string, TemplateInfo>>({});
  const [loading, setLoading] = useState(true);
  const [filterTemplate, setFilterTemplate] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  useEffect(() => {
    if (user && user.role !== "admin" && user.role !== "instructor") {
      router.push("/");
    }
  }, [user, router]);

  useEffect(() => {
    async function load() {
      try {
        const [sessData, tmplData, usersData] = await Promise.all([
          api.get<{ items: SessionItem[]; total: number }>("/sessions?page_size=100"),
          api.get<{ items: TemplateInfo[] }>("/templates"),
          api.get<{ items: UserInfo[] }>("/users?page_size=100"),
        ]);
        setSessions(sessData.items);
        const tMap: Record<string, TemplateInfo> = {};
        for (const t of tmplData.items) tMap[t.id] = t;
        setTemplates(tMap);
        const uMap: Record<string, UserInfo> = {};
        for (const u of usersData.items) uMap[u.id] = u;
        setUsers(uMap);
      } catch {
        // handled
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = sessions.filter((s) => {
    if (filterTemplate !== "all" && s.template_id !== filterTemplate) return false;
    if (filterStatus !== "all" && s.status !== filterStatus) return false;
    return true;
  });

  const graded = filtered.filter((s) => s.status === "graded" || s.status === "submitted");
  const avgScore = graded.length > 0
    ? graded.reduce((sum, s) => sum + (s.percentage ?? 0), 0) / graded.length
    : 0;
  const passCount = graded.filter((s) => s.passed === true).length;
  const passRate = graded.length > 0 ? (passCount / graded.length) * 100 : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p style={{ color: "var(--text-muted)" }}>Yükleniyor...</p>
      </div>
    );
  }

  const uniqueTemplates = Object.values(templates);

  return (
    <div className="space-y-6">
      <div>
        <h1
          className="text-2xl font-bold"
          style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}
        >
          Sınav Sonuçları
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          Tüm öğrencilerin sınav sonuçları ve istatistikleri.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Toplam Giriş" value={filtered.length} />
        <StatCard label="Tamamlanan" value={graded.length} />
        <StatCard label="Ort. Puan" value={`%${Math.round(avgScore)}`} />
        <StatCard label="Geçme Oranı" value={`%${Math.round(passRate)}`} accent={passRate >= 50} />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <select
          value={filterTemplate}
          onChange={(e) => setFilterTemplate(e.target.value)}
          className="rounded-md border px-3 py-2 text-sm"
          style={{
            borderColor: "var(--input-border)",
            backgroundColor: "var(--card)",
            color: "var(--text-primary)",
          }}
        >
          <option value="all">Tüm Sınavlar</option>
          {uniqueTemplates.map((t) => (
            <option key={t.id} value={t.id}>{t.title}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-md border px-3 py-2 text-sm"
          style={{
            borderColor: "var(--input-border)",
            backgroundColor: "var(--card)",
            color: "var(--text-primary)",
          }}
        >
          <option value="all">Tüm Durumlar</option>
          <option value="graded">Notlandırıldı</option>
          <option value="submitted">Tamamlandı</option>
          <option value="in_progress">Devam Ediyor</option>
          <option value="created">Oluşturuldu</option>
        </select>
      </div>

      {/* Results table */}
      <div
        className="rounded-lg border overflow-hidden"
        style={{ borderColor: "var(--border-light)" }}
      >
        <table className="w-full text-sm">
          <thead>
            <tr style={{ backgroundColor: "var(--card-hover)" }}>
              <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Öğrenci</th>
              <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Sınav</th>
              <th className="text-left px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Tarih</th>
              <th className="text-center px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Durum</th>
              <th className="text-center px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Puan</th>
              <th className="text-center px-4 py-3 font-medium" style={{ color: "var(--text-secondary)" }}>Sonuç</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8" style={{ color: "var(--text-muted)" }}>
                  Sonuç bulunamadı.
                </td>
              </tr>
            ) : (
              filtered.map((s) => {
                const u = users[s.user_id];
                const t = templates[s.template_id];
                const isFinished = s.status === "submitted" || s.status === "graded";
                return (
                  <tr
                    key={s.id}
                    className="border-t"
                    style={{ borderColor: "var(--border-light)" }}
                  >
                    <td className="px-4 py-3">
                      <div style={{ color: "var(--text-primary)" }}>{u?.full_name ?? "—"}</div>
                      <div className="text-xs" style={{ color: "var(--text-muted)" }}>{u?.email ?? ""}</div>
                    </td>
                    <td className="px-4 py-3" style={{ color: "var(--text-primary)" }}>
                      {t?.title ?? "—"}
                    </td>
                    <td className="px-4 py-3" style={{ color: "var(--text-muted)" }}>
                      {formatDate(s.submitted_at ?? s.started_at ?? s.created_at)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {s.percentage !== null ? (
                        <span
                          className="font-semibold"
                          style={{ color: s.passed ? "var(--success)" : "var(--danger)" }}
                        >
                          %{Math.round(s.percentage)}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {isFinished ? (
                        <Link
                          href={`/exam/${s.id}/result`}
                          className="text-xs font-medium px-3 py-1 rounded-md transition-colors"
                          style={{ backgroundColor: "var(--accent-light)", color: "var(--accent)" }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--accent)"; e.currentTarget.style.color = "white"; }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-light)"; e.currentTarget.style.color = "var(--accent)"; }}
                        >
                          Detay
                        </Link>
                      ) : (
                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div
      className="rounded-lg border p-4"
      style={{ backgroundColor: "var(--card)", borderColor: "var(--border-light)" }}
    >
      <div className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>{label}</div>
      <div
        className="text-2xl font-bold mt-1"
        style={{
          fontFamily: "var(--font-playfair), Georgia, serif",
          color: accent === true ? "var(--success)" : accent === false ? "var(--danger)" : "var(--text-primary)",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    created: { label: "Oluşturuldu", color: "var(--text-muted)", bg: "var(--border-light)" },
    in_progress: { label: "Devam Ediyor", color: "var(--warning)", bg: "var(--warning-light)" },
    submitted: { label: "Tamamlandı", color: "var(--accent)", bg: "var(--accent-light)" },
    graded: { label: "Notlandırıldı", color: "var(--special)", bg: "var(--special-light)" },
  };
  const s = map[status] ?? map.created;
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-medium"
      style={{ backgroundColor: s.bg, color: s.color }}
    >
      {s.label}
    </span>
  );
}
