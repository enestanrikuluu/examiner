"use client";

import { useEffect, useRef } from "react";
import { useExamSessionStore } from "@/lib/stores/exam-session-store";

interface IntegrityGuardProps {
  tabSwitchDetection: boolean;
  copyPasteBlock: boolean;
  fullscreenRequired: boolean;
}

export default function IntegrityGuard({
  tabSwitchDetection,
  copyPasteBlock,
  fullscreenRequired,
}: IntegrityGuardProps) {
  const addIntegrityEvent = useExamSessionStore((s) => s.addIntegrityEvent);
  const tabSwitchCount = useRef(0);

  // Tab switch / visibility change detection
  useEffect(() => {
    if (!tabSwitchDetection) return;

    function handleVisibilityChange() {
      if (document.hidden) {
        tabSwitchCount.current += 1;
        addIntegrityEvent({
          event_type: "tab_switch",
          details: { count: tabSwitchCount.current },
        });
      }
    }

    function handleBlur() {
      addIntegrityEvent({
        event_type: "focus_loss",
      });
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleBlur);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleBlur);
    };
  }, [tabSwitchDetection, addIntegrityEvent]);

  // Copy/paste blocking at document level
  useEffect(() => {
    if (!copyPasteBlock) return;

    function handleCopy(e: ClipboardEvent) {
      e.preventDefault();
      addIntegrityEvent({ event_type: "copy" });
    }

    function handlePaste(e: ClipboardEvent) {
      e.preventDefault();
      addIntegrityEvent({ event_type: "paste" });
    }

    function handleCut(e: ClipboardEvent) {
      e.preventDefault();
      addIntegrityEvent({ event_type: "cut" });
    }

    document.addEventListener("copy", handleCopy);
    document.addEventListener("paste", handlePaste);
    document.addEventListener("cut", handleCut);

    return () => {
      document.removeEventListener("copy", handleCopy);
      document.removeEventListener("paste", handlePaste);
      document.removeEventListener("cut", handleCut);
    };
  }, [copyPasteBlock, addIntegrityEvent]);

  // Fullscreen enforcement
  useEffect(() => {
    if (!fullscreenRequired) return;

    function requestFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
          // Fullscreen denied by browser
        });
      }
    }

    function handleFullscreenChange() {
      if (!document.fullscreenElement) {
        addIntegrityEvent({ event_type: "fullscreen_exit" });
        // Re-request fullscreen after brief delay
        setTimeout(requestFullscreen, 500);
      }
    }

    requestFullscreen();
    document.addEventListener("fullscreenchange", handleFullscreenChange);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {
          // ignore
        });
      }
    };
  }, [fullscreenRequired, addIntegrityEvent]);

  // Periodic integrity flush (every 30 seconds)
  useEffect(() => {
    const flushIntegrity = useExamSessionStore.getState().flushIntegrity;
    const interval = setInterval(() => {
      flushIntegrity();
    }, 30_000);
    return () => clearInterval(interval);
  }, []);

  // This component renders nothing visible
  return null;
}
