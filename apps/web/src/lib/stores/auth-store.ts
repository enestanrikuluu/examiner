import { create } from "zustand";
import { api, ApiError } from "@/lib/api-client";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  locale: string;
  is_active: boolean;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
    locale?: string
  ) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setTokens: (tokens: TokenResponse) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: false,
  isAuthenticated:
    typeof window !== "undefined" && !!localStorage.getItem("access_token"),

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const tokens = await api.post<TokenResponse>("/auth/login", {
        email,
        password,
      });
      get().setTokens(tokens);
      await get().fetchUser();
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (
    email: string,
    password: string,
    fullName: string,
    locale = "tr-TR"
  ) => {
    set({ isLoading: true });
    try {
      const tokens = await api.post<TokenResponse>("/auth/register", {
        email,
        password,
        full_name: fullName,
        locale,
      });
      get().setTokens(tokens);
      await get().fetchUser();
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const user = await api.get<User>("/users/me");
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  setTokens: (tokens: TokenResponse) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    set({ isAuthenticated: true });
  },
}));
