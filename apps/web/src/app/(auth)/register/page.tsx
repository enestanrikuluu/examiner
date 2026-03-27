"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Şifre en az 8 karakter olmalıdır");
      return;
    }
    try {
      await register(email, password, fullName);
      router.push("/exams");
    } catch {
      setError("Kayıt oluşturulamadı. Bu e-posta zaten kullanılıyor olabilir.");
    }
  };

  const inputStyle = {
    background: "var(--background)",
    border: "1px solid var(--input-border)",
    color: "var(--text-primary)",
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--input-focus)";
    e.target.style.boxShadow = "0 0 0 2px var(--accent-light)";
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--input-border)";
    e.target.style.boxShadow = "none";
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "var(--background)" }}>
      <div className="w-full max-w-md space-y-8">
        <div className="flex items-center justify-center gap-4">
          <div className="h-px flex-1" style={{ background: "var(--border)" }} />
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 0L12.47 7.53L20 10L12.47 12.47L10 20L7.53 12.47L0 10L7.53 7.53L10 0Z" fill="var(--accent)" />
          </svg>
          <div className="h-px flex-1" style={{ background: "var(--border)" }} />
        </div>

        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight" style={{ fontFamily: "var(--font-playfair), Georgia, serif", color: "var(--text-primary)" }}>
            AI Examiner
          </h1>
          <p className="mt-3 text-sm tracking-widest uppercase" style={{ color: "var(--text-muted)", letterSpacing: "0.15em" }}>
            Yeni hesap oluşturun
          </p>
        </div>

        <div className="rounded-xl p-8 shadow-sm" style={{ background: "var(--card)", border: "1px solid var(--border-light)" }}>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-lg text-sm" style={{ background: "var(--danger-light)", border: "1px solid #D4A0A8", color: "var(--danger)" }}>
                {error}
              </div>
            )}

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                Ad Soyad
              </label>
              <input
                id="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1.5 w-full rounded-lg px-4 py-2.5 text-sm transition-colors outline-none"
                style={inputStyle}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="Ad Soyad"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                E-posta
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-lg px-4 py-2.5 text-sm transition-colors outline-none"
                style={inputStyle}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="ornek@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                Şifre
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 w-full rounded-lg px-4 py-2.5 text-sm transition-colors outline-none"
                style={inputStyle}
                onFocus={handleFocus}
                onBlur={handleBlur}
                placeholder="En az 8 karakter"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg px-4 py-2.5 text-sm font-semibold tracking-wide uppercase transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "var(--accent)",
                color: "#FFFAF5",
                letterSpacing: "0.08em",
              }}
              onMouseEnter={(e) => { if (!isLoading) e.currentTarget.style.background = "var(--accent-hover)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "var(--accent)"; }}
            >
              {isLoading ? "Kayıt oluşturuluyor..." : "Kayıt Ol"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm" style={{ color: "var(--text-muted)" }}>
          Zaten hesabınız var mı?{" "}
          <Link href="/login" className="font-medium underline underline-offset-4 transition-colors" style={{ color: "var(--link)" }}>
            Giriş Yap
          </Link>
        </p>

        <div className="flex items-center justify-center gap-4">
          <div className="h-px flex-1" style={{ background: "var(--border)" }} />
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <circle cx="6" cy="6" r="3" fill="var(--border)" />
          </svg>
          <div className="h-px flex-1" style={{ background: "var(--border)" }} />
        </div>
      </div>
    </div>
  );
}
