import { useEffect, useRef, useState } from 'react';
import './styles.css';

type Category = { id: string; label: string; emoji: string; restricted?: boolean };
type Reel = {
  id: string;
  category: string;
  video_url: string;
  thumbnail_url?: string;
  title?: string;
};
type User = {
  id: number;
  name?: string;
  email?: string;
  picture?: string;
  age_eligible: boolean;
  onboarding_complete: boolean;
  countries: string[];
  category: string | null;
};
type Me = { authenticated: boolean; user: User | null };
type TelegramApi = {
  WebApp?: { initData?: string; ready: () => void; expand: () => void };
};

const countries = [
  ['NL', '🇳🇱', 'هولندا'], ['DE', '🇩🇪', 'ألمانيا'], ['FR', '🇫🇷', 'فرنسا'],
  ['GB', '🇬🇧', 'بريطانيا'], ['US', '🇺🇸', 'الولايات المتحدة'], ['CA', '🇨🇦', 'كندا'],
  ['TR', '🇹🇷', 'تركيا'], ['SA', '🇸🇦', 'السعودية'], ['AE', '🇦🇪', 'الإمارات'],
  ['EG', '🇪🇬', 'مصر'], ['IQ', '🇮🇶', 'العراق'], ['JO', '🇯🇴', 'الأردن'],
  ['MA', '🇲🇦', 'المغرب'], ['DZ', '🇩🇿', 'الجزائر'], ['TN', '🇹🇳', 'تونس'],
  ['ES', '🇪🇸', 'إسبانيا'], ['IT', '🇮🇹', 'إيطاليا'], ['SE', '🇸🇪', 'السويد'],
  ['NO', '🇳🇴', 'النرويج'], ['AU', '🇦🇺', 'أستراليا'],
] as const;

const categories: Category[] = [
  { id: 'all', label: 'الكل', emoji: '🔥' },
  { id: 'sports', label: 'رياضة', emoji: '⚽' },
  { id: 'gaming', label: 'ألعاب', emoji: '🎮' },
  { id: 'music', label: 'موسيقى', emoji: '🎵' },
  { id: 'entertainment', label: 'ترفيه', emoji: '😂' },
  { id: 'kids', label: 'أطفال', emoji: '👶' },
  { id: 'food', label: 'طبخ', emoji: '🍳' },
  { id: 'animals', label: 'حيوانات', emoji: '🐾' },
  { id: 'travel', label: 'سفر', emoji: '✈️' },
  { id: 'fitness', label: 'لياقة', emoji: '💪' },
  { id: 'adult', label: 'بالغين', emoji: '🔞', restricted: true },
];

const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const DRAFT_KEY = 'alibot-reels-onboarding-draft';
type OnboardingDraft = { countries?: string[]; category?: string; step?: 'countries' | 'category' };

export function App() {
  const [step, setStep] = useState<'countries' | 'category' | 'feed'>('countries');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [category, setCategory] = useState('all');
  const [reels, setReels] = useState<Reel[]>([]);
  const [active, setActive] = useState(0);
  const [me, setMe] = useState<Me>({ authenticated: false, user: null });
  const [authLoading, setAuthLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const videos = useRef<Array<HTMLVideoElement | null>>([]);

  const loadFeed = async (nextCategory = category) => {
    setLoading(true);
    setError('');
    setActive(0);
    setReels([]);
    try {
      const response = await fetch(
        API + '/api/feed?category=' + encodeURIComponent(nextCategory),
        { credentials: 'include' },
      );
      if (response.status === 403) throw new Error('AGE_REQUIRED');
      if (response.status === 401 || response.status === 409) throw new Error('ONBOARDING_REQUIRED');
      if (!response.ok) throw new Error('FEED');
      const data = await response.json();
      setReels(Array.isArray(data.items) ? data.items : []);
    } catch (err) {
      const code = err instanceof Error ? err.message : 'FEED';
      setError(code === 'AGE_REQUIRED' ? 'AGE_REQUIRED' : code === 'ONBOARDING_REQUIRED' ? 'ONBOARDING_REQUIRED' : 'FEED');
    } finally {
      setLoading(false);
    }
  };

  const refreshMe = async () => {
    const response = await fetch(API + '/api/me', { credentials: 'include' });
    if (!response.ok) return null;
    const current = (await response.json()) as Me;
    setMe(current);
    return current;
  };

  useEffect(() => {
    const telegram = (window as Window & { Telegram?: TelegramApi }).Telegram?.WebApp;
    telegram?.ready();
    telegram?.expand();

    const authenticate = async () => {
      try {
        if (telegram?.initData) {
          const response = await fetch(API + '/api/auth/telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ init_data: telegram.initData }),
          });
          if (!response.ok) {
            await refreshMe();
            return;
          }
        }

        const current = await refreshMe();
        if (current?.authenticated && current.user?.onboarding_complete && current.user.category && current.user.countries.length) {
          setSelectedCountries(current.user.countries);
          setCategory(current.user.category);
          setStep('feed');
          await loadFeed(current.user.category);
          sessionStorage.removeItem(DRAFT_KEY);
          return;
        }

        const rawDraft = sessionStorage.getItem(DRAFT_KEY);
        if (rawDraft) {
          try {
            const draft = JSON.parse(rawDraft) as OnboardingDraft;
            if (Array.isArray(draft.countries)) setSelectedCountries(draft.countries);
            if (typeof draft.category === 'string') setCategory(draft.category);
            if (draft.step === 'category' && Array.isArray(draft.countries) && draft.countries.length) setStep('category');
          } catch {
            sessionStorage.removeItem(DRAFT_KEY);
          }
        }
      } finally {
        setAuthLoading(false);
      }
    };

    void authenticate();
  }, []);

  const persistOnboarding = async (nextCategory: string) => {
    const response = await fetch(API + '/api/onboarding', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ countries: selectedCountries, category: nextCategory }),
    });
    if (response.status === 403) throw new Error('AGE_REQUIRED');
    if (!response.ok) throw new Error('ONBOARDING_SAVE');
  };

  const completeCountries = () => {
    if (!selectedCountries.length) {
      setError('COUNTRIES_REQUIRED');
      return;
    }
    setError('');
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ countries: selectedCountries, category, step: 'category' }));
    setStep('category');
  };

  const completeCategory = async (choice: Category) => {
    if (choice.restricted && !me.user?.age_eligible) {
      setError('AGE_REQUIRED');
      return;
    }
    if (!me.authenticated) {
      sessionStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({ countries: selectedCountries, category: choice.id, step: 'category' }),
      );
      setError('LOGIN_REQUIRED');
      return;
    }

    setError('');
    try {
      await persistOnboarding(choice.id);
      sessionStorage.removeItem(DRAFT_KEY);
      setCategory(choice.id);
      setStep('feed');
      await loadFeed(choice.id);
    } catch (err) {
      const code = err instanceof Error ? err.message : 'ONBOARDING_SAVE';
      setError(code);
    }
  };

  const login = () => {
    sessionStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({ countries: selectedCountries, category }),
    );
    window.location.href = API + '/api/auth/google/login';
  };

  const selectCountry = (code: string) => {
    setError('');
    setSelectedCountries((current) =>
      current.includes(code) ? current.filter((value) => value !== code) : [...current, code],
    );
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.65) {
          const index = Number((entry.target as HTMLElement).dataset.index);
          if (Number.isFinite(index)) setActive(index);
        }
      }),
      { threshold: [0.65] },
    );
    videos.current.forEach((video) => video && observer.observe(video));
    return () => observer.disconnect();
  }, [reels]);

  useEffect(() => {
    videos.current.forEach((video, index) => {
      if (!video) return;
      if (index === active) {
        video.muted = true;
        void video.play().catch(() => undefined);
      } else {
        video.pause();
        video.currentTime = 0;
      }
    });
  }, [active, reels]);

  if (authLoading) {
    return <main className="onboarding"><div className="loading-card">جارٍ تجهيز حسابك…</div></main>;
  }

  if (step !== 'feed') {
    return (
      <main className="onboarding">
        <section className="onboarding-card">
          <div className="brand">AliBot Reels</div>

          {step === 'countries' ? (
            <>
              <span className="step">الخطوة 1 من 2</span>
              <h1>من أي بلدان تريد مشاهدة المحتوى؟</h1>
              <p>اختر بلداً واحداً أو عدة بلدان. هذا الاختيار سيحدد مصادر المحتوى في الـFeed.</p>
              <div className="country-grid">
                {countries.map(([code, flag, label]) => (
                  <button
                    key={code}
                    className={selectedCountries.includes(code) ? 'country selected' : 'country'}
                    onClick={() => selectCountry(code)}
                  >
                    <span>{flag}</span>
                    <b>{label}</b>
                    {selectedCountries.includes(code) && <i>✓</i>}
                  </button>
                ))}
              </div>
              {error === 'COUNTRIES_REQUIRED' && <div className="notice">اختر بلداً واحداً على الأقل.</div>}
              <button className="continue" disabled={!selectedCountries.length} onClick={completeCountries}>
                متابعة <span>←</span>
              </button>
            </>
          ) : (
            <>
              <span className="step">الخطوة 2 من 2</span>
              <h1>ما نوع المحتوى الذي تفضله؟</h1>
              <p>سيتم حفظ الفئة مع البلدان المختارة، ويُطبّق كلاهما على الـFeed.</p>
              <div className="category-grid">
                {categories.map((choice) => (
                  <button key={choice.id} className="choice" onClick={() => completeCategory(choice)}>
                    {choice.emoji}
                    <b>{choice.label}</b>
                  </button>
                ))}
              </div>
              {error === 'AGE_REQUIRED' && <div className="notice">هذه الفئة تتطلب تسجيل الدخول وتأكيد الأهلية العمرية.</div>}
              {error === 'LOGIN_REQUIRED' && (
                <div className="notice">
                  سجّل الدخول أولاً لحفظ تفضيلاتك وتشغيل الـFeed المخصص.
                  <button className="auth-inline" onClick={login}>تسجيل الدخول بـ Google</button>
                </div>
              )}
              {error === 'ONBOARDING_SAVE' && <div className="notice">تعذر حفظ التفضيلات. حاول مرة أخرى.</div>}
              <button className="back" onClick={() => { setError(''); setStep('countries'); }}>
                → العودة لاختيار البلدان
              </button>
            </>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <strong>AliBot Reels</strong>
        <button className="login" onClick={login}>
          {me.authenticated ? (me.user?.name || 'حسابي') : 'تسجيل Google'}
        </button>
      </header>

      <nav className="categories">
        {categories.map((choice) => (
          <button
            key={choice.id}
            className={category === choice.id ? 'cat active' : 'cat'}
            onClick={() => void completeCategory(choice)}
          >
            {choice.emoji} {choice.label}
          </button>
        ))}
      </nav>

      <section className="feed" aria-label="الفيديوهات">
        {loading && <div className="empty">جارٍ تحميل القائمة…</div>}
        {!loading && !error && reels.length === 0 && (
          <div className="empty">لا توجد فيديوهات منشورة مطابقة لبلدانك وفئتك حالياً.</div>
        )}
        {!loading && error === 'AGE_REQUIRED' && (
          <div className="empty">هذه الفئة تتطلب الأهلية العمرية.</div>
        )}
        {!loading && error === 'FEED' && <div className="empty">تعذر تحميل القائمة حالياً.</div>}
        {reels.map((reel, index) => (
          <article className="reel" key={reel.id}>
            <video
              ref={(element) => { videos.current[index] = element; }}
              data-index={index}
              src={reel.video_url}
              poster={reel.thumbnail_url}
              playsInline
              muted
              controls={false}
              preload={index === active + 1 ? 'metadata' : index === active ? 'auto' : 'none'}
            />
            <div className="shade" />
            {reel.title && <div className="caption">{reel.title}</div>}
          </article>
        ))}
      </section>
    </main>
  );
}
