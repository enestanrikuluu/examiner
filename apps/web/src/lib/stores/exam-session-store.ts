import { create } from "zustand";
import { api } from "@/lib/api-client";
import type {
  ExamSession,
  QuestionItem,
  SessionResponse,
} from "@/types";

interface FeatureFlags {
  proctoring_enabled: boolean;
  tab_switch_detection: boolean;
  copy_paste_block: boolean;
  fullscreen_required: boolean;
}

interface IntegrityEvent {
  event_type: string;
  details?: Record<string, unknown>;
}

interface ExamSessionState {
  // Session data
  session: ExamSession | null;
  questions: QuestionItem[];
  answers: Record<string, Record<string, unknown>>;
  flags: FeatureFlags | null;

  // UI state
  currentIndex: number;
  loading: boolean;
  submitting: boolean;
  error: string | null;

  // Integrity
  integrityQueue: IntegrityEvent[];

  // Actions
  initialize: (sessionId: string) => Promise<void>;
  setCurrentIndex: (index: number) => void;
  saveAnswer: (questionId: string, answer: Record<string, unknown>) => void;
  toggleFlag: (questionId: string) => void;
  submitExam: () => Promise<void>;
  heartbeat: () => Promise<void>;
  addIntegrityEvent: (event: IntegrityEvent) => void;
  flushIntegrity: () => Promise<void>;

  // Autosave internals
  _pendingSaves: Set<string>;
  _flushSave: (questionId: string) => Promise<void>;
}

// Debounce timers stored outside Zustand to avoid serialization issues
const saveTimers: Record<string, ReturnType<typeof setTimeout>> = {};
const AUTOSAVE_DELAY_MS = 1500;

export const useExamSessionStore = create<ExamSessionState>((set, get) => ({
  session: null,
  questions: [],
  answers: {},
  flags: null,
  currentIndex: 0,
  loading: true,
  submitting: false,
  error: null,
  integrityQueue: [],
  _pendingSaves: new Set(),

  initialize: async (sessionId: string) => {
    set({ loading: true, error: null });
    try {
      // Load feature flags and resume session in parallel
      const [flagsData, resumeData] = await Promise.all([
        api.get<FeatureFlags>("/sessions/feature-flags"),
        api.get<{ session: ExamSession; responses: SessionResponse[] }>(
          `/sessions/${sessionId}/resume`
        ),
      ]);

      const sess = resumeData.session;
      set({ flags: flagsData });

      // If already submitted/graded, signal to caller
      if (sess.status === "submitted" || sess.status === "graded") {
        set({ session: sess, loading: false });
        return;
      }

      // Load questions
      const qData = await api.get<{ items: QuestionItem[]; total: number }>(
        `/templates/${sess.template_id}/questions`
      );

      // Reorder based on session question_order
      let ordered = qData.items;
      if (sess.question_order) {
        const qMap = new Map(qData.items.map((q) => [q.id, q]));
        ordered = sess.question_order
          .map((id) => qMap.get(id))
          .filter((q): q is QuestionItem => q !== undefined);
      }

      // Restore existing answers from resumed responses
      const restoredAnswers: Record<string, Record<string, unknown>> = {};
      for (const resp of resumeData.responses) {
        restoredAnswers[resp.question_id] = resp.answer;
      }

      set({
        session: sess,
        questions: ordered,
        answers: restoredAnswers,
        loading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Sınav yüklenemedi",
        loading: false,
      });
    }
  },

  setCurrentIndex: (index: number) => {
    set({ currentIndex: index });
  },

  saveAnswer: (questionId: string, answer: Record<string, unknown>) => {
    // Update local state immediately
    set((state) => ({
      answers: { ...state.answers, [questionId]: answer },
    }));

    // Debounced server save
    if (saveTimers[questionId]) {
      clearTimeout(saveTimers[questionId]);
    }
    saveTimers[questionId] = setTimeout(() => {
      get()._flushSave(questionId);
    }, AUTOSAVE_DELAY_MS);
  },

  _flushSave: async (questionId: string) => {
    const state = get();
    const answer = state.answers[questionId];
    const sessionId = state.session?.id;
    if (!answer || !sessionId) return;

    state._pendingSaves.add(questionId);
    try {
      await api.post(`/sessions/${sessionId}/responses`, {
        question_id: questionId,
        answer,
      });
    } catch {
      // Autosave failure is silent; answer is preserved in local state
    } finally {
      state._pendingSaves.delete(questionId);
    }
  },

  toggleFlag: (questionId: string) => {
    const state = get();
    const sessionId = state.session?.id;
    if (!sessionId) return;

    const currentAnswer = state.answers[questionId];
    // We save a flag toggle via the response API
    api
      .post(`/sessions/${sessionId}/responses`, {
        question_id: questionId,
        answer: currentAnswer || {},
        is_flagged: true,
      })
      .catch(() => {
        // silent
      });
  },

  submitExam: async () => {
    const state = get();
    const sessionId = state.session?.id;
    if (!sessionId) return;

    set({ submitting: true });

    // Flush all pending saves first
    for (const qId of Object.keys(saveTimers)) {
      clearTimeout(saveTimers[qId]);
      delete saveTimers[qId];
    }

    // Save all answers that have pending timers
    const savePromises = Object.entries(state.answers).map(([qId, answer]) =>
      api
        .post(`/sessions/${sessionId}/responses`, {
          question_id: qId,
          answer,
        })
        .catch(() => {
          // ignore save errors on submit
        })
    );
    await Promise.all(savePromises);

    // Flush integrity events
    await get().flushIntegrity();

    try {
      const updated = await api.post<ExamSession>(
        `/sessions/${sessionId}/submit`
      );
      set({ session: updated, submitting: false });
    } catch (err) {
      set({
        submitting: false,
        error: err instanceof Error ? err.message : "Gönderme hatası",
      });
    }
  },

  heartbeat: async () => {
    const state = get();
    const sessionId = state.session?.id;
    if (!sessionId || state.session?.status !== "in_progress") return;

    try {
      const result = await api.post<{
        status: string;
        remaining_seconds: number | null;
      }>(`/sessions/${sessionId}/heartbeat`);

      if (result.status === "submitted") {
        set((prev) => ({
          session: prev.session
            ? { ...prev.session, status: "submitted" }
            : null,
        }));
      }
    } catch {
      // heartbeat failure is silent
    }
  },

  addIntegrityEvent: (event: IntegrityEvent) => {
    set((state) => ({
      integrityQueue: [...state.integrityQueue, event],
    }));

    // Auto-flush when queue reaches 10
    if (get().integrityQueue.length >= 10) {
      get().flushIntegrity();
    }
  },

  flushIntegrity: async () => {
    const state = get();
    const sessionId = state.session?.id;
    const events = state.integrityQueue;
    if (!sessionId || events.length === 0) return;

    set({ integrityQueue: [] });
    try {
      await api.post(`/sessions/${sessionId}/integrity`, { events });
    } catch {
      // re-queue on failure
      set((prev) => ({
        integrityQueue: [...events, ...prev.integrityQueue],
      }));
    }
  },
}));
