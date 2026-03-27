"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      router.push("/exams");
    } catch {
      setError("Geçersiz e-posta veya şifre");
    }
  };

  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

  const handleGoogleLogin = async () => {
    try {
      const res = await fetch(`${API_URL}/auth/google`);
      const data = await res.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch {
      setError("Google ile giriş yapılamadı");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "var(--background)" }}>
      <div className="w-full max-w-md space-y-8">
        {/* Decorative top line */}
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
            Hesabınıza giriş yapın
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
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--input-border)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => { e.target.style.borderColor = "var(--input-focus)"; e.target.style.boxShadow = "0 0 0 2px var(--accent-light)"; }}
                onBlur={(e) => { e.target.style.borderColor = "var(--input-border)"; e.target.style.boxShadow = "none"; }}
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 w-full rounded-lg px-4 py-2.5 text-sm transition-colors outline-none"
                style={{
                  background: "var(--background)",
                  border: "1px solid var(--input-border)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => { e.target.style.borderColor = "var(--input-focus)"; e.target.style.boxShadow = "0 0 0 2px var(--accent-light)"; }}
                onBlur={(e) => { e.target.style.borderColor = "var(--input-border)"; e.target.style.boxShadow = "none"; }}
                placeholder="••••••••"
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
              {isLoading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full" style={{ borderTop: "1px solid var(--border)" }} />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3" style={{ background: "var(--card)", color: "var(--text-muted)" }}>veya</span>
            </div>
          </div>

          <button
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
            style={{
              background: "var(--background)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "var(--card-hover)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "var(--background)"; }}
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Google ile Giriş Yap
          </button>
        </div>

        <p className="text-center text-sm" style={{ color: "var(--text-muted)" }}>
          Hesabınız yok mu?{" "}
          <Link href="/register" className="font-medium underline underline-offset-4 transition-colors" style={{ color: "var(--link)" }}>
            Kayıt Ol
          </Link>
        </p>

        {/* Decorative bottom line */}
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
