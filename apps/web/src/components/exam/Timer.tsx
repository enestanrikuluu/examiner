"use client";

import { useEffect, useState, useCallback } from "react";

interface TimerProps {
  expiresAt: string | null;
  onExpire: () => void;
  warningThresholdSeconds?: number;
}

export default function Timer({
  expiresAt,
  onExpire,
  warningThresholdSeconds = 300,
}: TimerProps) {
  const [remaining, setRemaining] = useState<number | null>(null);

  const calcRemaining = useCallback(() => {
    if (!expiresAt) return null;
    const diff = new Date(expiresAt).getTime() - Date.now();
    return Math.max(0, Math.floor(diff / 1000));
  }, [expiresAt]);

  useEffect(() => {
    if (!expiresAt) return;

    setRemaining(calcRemaining());

    const interval = setInterval(() => {
      const r = calcRemaining();
      setRemaining(r);
      if (r !== null && r <= 0) {
        clearInterval(interval);
        onExpire();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt, calcRemaining, onExpire]);

  if (remaining === null) return null;

  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  const seconds = remaining % 60;

  const isWarning = remaining <= warningThresholdSeconds;
  const isCritical = remaining <= 60;

  const timeStr =
    hours > 0
      ? `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
      : `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-sm font-mono font-medium ${
        isCritical
          ? "bg-red-100 text-red-700 animate-pulse"
          : isWarning
            ? "bg-amber-100 text-amber-700"
            : "bg-gray-100 text-gray-700"
      }`}
    >
      <svg
        className="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
        />
      </svg>
      {timeStr}
    </div>
  );
}
