"use client";

import { useAuthStore } from "@/lib/stores/auth-store";

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Hoş geldiniz{user ? `, ${user.full_name}` : ""}
        </h1>
        <p className="mt-1 text-gray-600">
          AI Examiner ile sınav oluşturun, yönetin ve analiz edin.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900">Sınavlarım</h3>
          <p className="mt-1 text-sm text-gray-600">
            Aktif ve tamamlanmış sınavlarınızı görüntüleyin.
          </p>
        </div>

        {user && (user.role === "instructor" || user.role === "admin") && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900">Sınav Oluştur</h3>
            <p className="mt-1 text-sm text-gray-600">
              AI destekli soru oluşturma ile yeni sınav hazırlayın.
            </p>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900">Sonuçlar</h3>
          <p className="mt-1 text-sm text-gray-600">
            Sınav sonuçlarınızı ve performans analizlerinizi inceleyin.
          </p>
        </div>
      </div>
    </div>
  );
}
