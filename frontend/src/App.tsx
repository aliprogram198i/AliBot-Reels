import { useEffect, useMemo, useRef, useState } from 'react';
import './styles.css';

type Category = { id: string; label: string; emoji: string; restricted?: boolean };
type Reel = { id: string; category: string; video_url: string; thumbnail_url?: string; title?: string };
type Me = { authenticated: boolean; user: { name?: string; email?: string; picture?: string; age_eligible: boolean } | null };

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

export function App() {
  const [category, setCategory] = useState('all');
  const [reels, setReels] = useState<Reel[]>([]);
  const [active, setActive] = useState(0);
  const [me, setMe] = useState<Me>({ authenticated: false, user: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const videos = useRef<Array<HTMLVideoElement | null>>([]);

  const visibleCategories = useMemo(() => categories, []);

  useEffect(() => {
    fetch(API + '/api/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('auth')))
      .then(setMe)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    setActive(0);
    fetch(API + '/api/feed?category=' + encodeURIComponent(category), {
      signal: controller.signal,
      credentials: 'include',
    })
      .then(async r => {
        if (r.status === 403) throw new Error('AGE_REQUIRED');
        if (!r.ok) throw new Error('FEED');
        return r.json();
      })
      .then(data => setReels(Array.isArray(data.items) ? data.items : []))
      .catch(err => {
        if (err.name !== 'AbortError') {
          setReels([]);
          setError(err.message === 'AGE_REQUIRED' ? 'AGE_REQUIRED' : 'FEED');
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [category]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(entry => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.65) {
          const index = Number((entry.target as HTMLElement).dataset.index);
          if (Number.isFinite(index)) setActive(index);
        }
      }),
      { threshold: [0.65] },
    );
    videos.current.forEach(video => {
      if (video) observer.observe(video);
    });
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

  const login = () => {
    window.location.href = API + '/api/auth/google/login';
  };

  const logout = async () => {
    await fetch(API + '/api/auth/logout', { method: 'POST', credentials: 'include' });
    setMe({ authenticated: false, user: null });
    if (category === 'adult') setCategory('all');
  };

  const unlockAdult = async () => {
    if (!me.authenticated) {
      login();
      return;
    }
    const response = await fetch(API + '/api/me/age-eligibility', {
      method: 'POST',
      credentials: 'include',
    });
    if (response.ok) {
      setMe(current => ({ ...current, user: current.user ? { ...current.user, age_eligible: true } : null }));
      setCategory('adult');
      setError('');
    }
  };

  const selectCategory = (c: Category) => {
    if (c.restricted && !me.user?.age_eligible) {
      setError('AGE_REQUIRED');
      return;
    }
    setCategory(c.id);
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <strong>AliBot Reels</strong>
        {me.authenticated ? (
          <button className="login" onClick={logout}>{me.user?.name || 'حسابي'} · خروج</button>
        ) : (
          <button className="login" onClick={login}>تسجيل Google</button>
        )}
      </header>

      <nav className="categories" aria-label="الفئات">
        {visibleCategories.map(c => (
          <button key={c.id} className={category === c.id ? 'cat active' : 'cat'} onClick={() => selectCategory(c)}>
            {c.emoji} {c.label}
          </button>
        ))}
      </nav>

      {error === 'AGE_REQUIRED' && (
        <section className="modal-backdrop">
          <div className="age-gate">
            <h2>محتوى مقيّد بالعمر</h2>
            <p>تسجيل Google مطلوب قبل تفعيل أهلية الوصول إلى هذه الفئة.</p>
            <div className="gate-actions">
              <button onClick={me.authenticated ? unlockAdult : login}>{me.authenticated ? 'تأكيد الأهلية' : 'تسجيل Google'}</button>
              <button className="secondary" onClick={() => setError('')}>إلغاء</button>
            </div>
          </div>
        </section>
      )}

      <section className="feed" aria-label="الفيديوهات">
        {loading && <div className="empty">جارٍ تحميل القائمة…</div>}
        {!loading && !error && reels.length === 0 && <div className="empty">لا توجد فيديوهات منشورة في هذه الفئة حالياً.</div>}
        {!loading && error === 'FEED' && <div className="empty">تعذر تحميل القائمة حالياً.</div>}

        {reels.map((reel, i) => (
          <article className="reel" key={reel.id}>
            <video
              ref={element => { videos.current[i] = element; }}
              data-index={i}
              src={reel.video_url}
              poster={reel.thumbnail_url}
              playsInline
              muted
              controls={false}
              preload={i === active + 1 ? 'metadata' : i === active ? 'auto' : 'none'}
            />
            <div className="shade" />
            {reel.title && <div className="caption">{reel.title}</div>}
          </article>
        ))}
      </section>
    </main>
  );
}
