"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/Toast";

interface UserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface UserListResponse {
  items: UserItem[];
  total: number;
  page: number;
  page_size: number;
}

const ROLES = ["student", "instructor", "admin"];

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function AdminUsersPage() {
  const { user } = useAuthStore();
  const router = useRouter();
  const toast = useToast();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState("");
  const pageSize = 20;

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/");
    }
  }, [user, router]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await api.get<UserListResponse>(
        `/users?page=${page}&page_size=${pageSize}`
      );
      setUsers(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Kullanıcılar yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") {
      fetchUsers();
    }
  }, [page, user]);

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await api.patch(`/users/${userId}`, { role: newRole });
      toast.success("Rol güncellendi");
      setEditingId(null);
      fetchUsers();
    } catch {
      toast.error("Rol güncellenemedi");
    }
  };

  const handleToggleActive = async (u: UserItem) => {
    try {
      await api.patch(`/users/${u.id}`, { is_active: !u.is_active });
      toast.success(u.is_active ? "Kullanıcı devre dışı bırakıldı" : "Kullanıcı aktif edildi");
      fetchUsers();
    } catch {
      toast.error("İşlem başarısız");
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  if (user?.role !== "admin") return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)", fontFamily: "var(--font-playfair), Georgia, serif" }}
          >
            Kullanıcı Yönetimi
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
            {total} kullanıcı kayıtlı
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div
            className="w-8 h-8 border-2 rounded-full animate-spin"
            style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }}
          />
        </div>
      ) : (
        <>
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "var(--card)", border: "1px solid var(--border)" }}
          >
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  <th className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    Kullanıcı
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    Rol
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    Durum
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    Kayıt Tarihi
                  </th>
                  <th className="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    İşlemler
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr
                    key={u.id}
                    style={{ borderBottom: "1px solid var(--border)" }}
                    className="transition-colors"
                    onMouseEnter={(e) => { e.currentTarget.style.background = "var(--card-hover)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                  >
                    <td className="px-5 py-4">
                      <div className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
                        {u.full_name}
                      </div>
                      <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {u.email}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {editingId === u.id ? (
                        <select
                          value={editRole}
                          onChange={(e) => {
                            handleRoleChange(u.id, e.target.value);
                          }}
                          onBlur={() => setEditingId(null)}
                          autoFocus
                          className="text-sm rounded-md px-2 py-1"
                          style={{
                            background: "var(--background)",
                            color: "var(--text-primary)",
                            border: "1px solid var(--accent)",
                          }}
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r === "admin" ? "Admin" : r === "instructor" ? "Öğretmen" : "Öğrenci"}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium cursor-pointer"
                          style={{
                            background: u.role === "admin"
                              ? "rgba(239, 68, 68, 0.1)"
                              : u.role === "instructor"
                              ? "rgba(59, 130, 246, 0.1)"
                              : "rgba(34, 197, 94, 0.1)",
                            color: u.role === "admin"
                              ? "#ef4444"
                              : u.role === "instructor"
                              ? "#3b82f6"
                              : "#22c55e",
                          }}
                          onClick={() => {
                            if (u.id !== user?.id) {
                              setEditingId(u.id);
                              setEditRole(u.role);
                            }
                          }}
                          title={u.id === user?.id ? "Kendi rolünüzü değiştiremezsiniz" : "Rol değiştirmek için tıklayın"}
                        >
                          {u.role === "admin" ? "Admin" : u.role === "instructor" ? "Öğretmen" : "Öğrenci"}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className="inline-flex items-center gap-1.5 text-xs font-medium"
                        style={{ color: u.is_active ? "#22c55e" : "#ef4444" }}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ background: u.is_active ? "#22c55e" : "#ef4444" }}
                        />
                        {u.is_active ? "Aktif" : "Devre Dışı"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm" style={{ color: "var(--text-secondary)" }}>
                      {formatDate(u.created_at)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {u.id !== user?.id && (
                        <button
                          onClick={() => handleToggleActive(u)}
                          className="text-xs font-medium px-3 py-1.5 rounded-md transition-colors"
                          style={{
                            background: u.is_active ? "rgba(239, 68, 68, 0.1)" : "rgba(34, 197, 94, 0.1)",
                            color: u.is_active ? "#ef4444" : "#22c55e",
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.8"; }}
                          onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
                        >
                          {u.is_active ? "Devre Dışı Bırak" : "Aktif Et"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors disabled:opacity-40"
                style={{ background: "var(--card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
              >
                Önceki
              </button>
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 rounded-md text-sm font-medium transition-colors disabled:opacity-40"
                style={{ background: "var(--card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
              >
                Sonraki
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
