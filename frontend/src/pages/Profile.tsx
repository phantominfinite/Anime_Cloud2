import { useEffect, useState } from 'react';
import { getMe, getTelegramInitData } from '../services/api';
import { Shield, User as UserIcon } from 'lucide-react';

export default function Profile() {
  const [me, setMe] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const initData = getTelegramInitData();

  useEffect(() => {
    const run = async () => {
      if (!initData) return;
      try {
        const res = await getMe();
        setMe(res.user || res);
      } catch (e: any) {
        setError(e?.message || 'Failed to load profile');
      }
    };
    run();
  }, [initData]);

  return (
    <div className="px-4 py-10 pb-24 text-white max-w-2xl mx-auto">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 rounded-2xl bg-white/10 flex items-center justify-center">
          <UserIcon className="w-6 h-6" />
        </div>
        <div>
          <div className="text-xl font-bold">پروفایل</div>
          <div className="text-xs text-white/60">وضعیت اتصال تلگرام و اطلاعات کاربر</div>
        </div>
      </div>

      {!initData ? (
        <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
          برای دیدن اطلاعات پروفایل باید پروژه را از داخل Telegram Mini App باز کنید (initData در مرورگر معمولی وجود ندارد).
        </div>
      ) : error ? (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-5">
          {me ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm text-white/70">نام</div>
                <div className="text-sm font-semibold">{me.first_name || '—'}</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-white/70">یوزرنیم</div>
                <div className="text-sm font-semibold">{me.username ? `@${me.username}` : '—'}</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-white/70">Telegram ID</div>
                <div className="text-sm font-semibold">{me.telegram_id || '—'}</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-white/70">دسترسی</div>
                <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs">
                  <Shield className="w-4 h-4" />
                  {me.is_admin ? 'ادمین' : 'کاربر'}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-white/70">در حال دریافت...</div>
          )}
        </div>
      )}
    </div>
  );
}
