"use client";

import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
          Hoş geldiniz{user ? `, ${user.full_name}` : ""}
        </h1>
        <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
          AI Examiner ile sınav oluşturun, yönetin ve analiz edin.
        </p>
      </div>

      {/* Decorative divider */}
      <div className="flex items-center gap-4">
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 0L9.8 6.2L16 8L9.8 9.8L8 16L6.2 9.8L0 8L6.2 6.2L8 0Z" fill="var(--border)" />
        </svg>
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/exams"
          className="group rounded-xl p-6 transition-all duration-200"
          style={{ background: "var(--card)", border: "1px solid var(--border-light)" }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(139, 105, 20, 0.08)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-light)"; e.currentTarget.style.boxShadow = "none"; }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: "var(--accent-light)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
          <h3 className="font-semibold" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
            Sınavlar
          </h3>
          <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
            Sınav şablonlarını görüntüleyin ve yönetin.
          </p>
        </Link>

        {user && (user.role === "instructor" || user.role === "admin") && (
          <Link
            href="/exams/new"
            className="group rounded-xl p-6 transition-all duration-200"
            style={{ background: "var(--card)", border: "1px solid var(--border-light)" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(139, 105, 20, 0.08)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-light)"; e.currentTarget.style.boxShadow = "none"; }}
          >
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: "var(--success-light)" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </div>
            <h3 className="font-semibold" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
              Sınav Oluştur
            </h3>
            <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
              AI destekli soru oluşturma ile yeni sınav hazırlayın.
            </p>
          </Link>
        )}

        <Link
          href="/my-exams"
          className="group rounded-xl p-6 transition-all duration-200"
          style={{ background: "var(--card)", border: "1px solid var(--border-light)" }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(139, 105, 20, 0.08)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-light)"; e.currentTarget.style.boxShadow = "none"; }}
        >
          <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: "var(--special-light)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--special)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <h3 className="font-semibold" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
            Sonuçlar
          </h3>
          <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
            Sınav sonuçlarınızı ve performans analizlerinizi inceleyin.
          </p>
        </Link>

        {user && (user.role === "instructor" || user.role === "admin") && (
          <Link
            href="/analytics"
            className="group rounded-xl p-6 transition-all duration-200"
            style={{ background: "var(--card)", border: "1px solid var(--border-light)" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(139, 105, 20, 0.08)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-light)"; e.currentTarget.style.boxShadow = "none"; }}
          >
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: "var(--info-light)" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--info)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="2" x2="12" y2="22" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <h3 className="font-semibold" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
              Analitik
            </h3>
            <p className="mt-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
              Sınav istatistikleri ve performans raporları.
            </p>
          </Link>
        )}
      </div>
    </div>
  );
}
