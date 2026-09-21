import { useEffect, useMemo, useState } from 'react';
import './styles.css';

type Category = { id: string; label: string; emoji: string; restricted?: boolean };
type Reel = { id: string; category: string; video_url: string; thumbnail_url?: string; title?: string };

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

const demo: Reel[] = [];

export function App() {
  const [category, setCategory] = useState('all');
  const [ageEligible, setAgeEligible] = useState(false);
  const [reels, setReels] = useState<Reel[]>(demo);
  const [active, setActive] = useState(0);

  const visibleCategories = useMemo(() => categories, []);

  useEffect(() => {
    setActive(0);
    // Feed API integration is intentionally isolated from playback.
    const controller = new AbortController();
    fetch(`/api/feed?category=${encodeURIComponent(category)}`, { signal: controller.signal })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('feed')))
      .then(data => setReels(Array.isArray(data.items) ? data.items : []))
      .catch(() => setReels([]));
    return () => controller.abort();
  }, [category]);

  const selectCategory = (c: Category) => {
    if (c.restricted && !ageEligible) return;
    setCategory(c.id);
  };

  return <main className="app-shell">
    <header className="topbar"><strong>AliBot Reels</strong><button className="login">تسجيل Google</button></header>
    <nav className="categories" aria-label="الفئات">
      {visibleCategories.map(c => <button key={c.id} className={category === c.id ? 'cat active' : 'cat'} onClick={() => selectCategory(c)}>{c.emoji} {c.label}</button>)}
    </nav>
    {category === 'adult' && !ageEligible && <section className="age-gate"><h2>محتوى مقيّد بالعمر</h2><p>يلزم تأكيد أهلية العمر قبل الوصول إلى هذه الفئة.</p><button onClick={() => setAgeEligible(true)}>أنا مؤهل للوصول</button></section>}
    <section className="feed" aria-label="الفيديوهات">
      {reels.length === 0 ? <div className="empty">لا توجد فيديوهات متاحة في هذه الفئة حالياً.</div> : reels.map((reel, i) => <article className="reel" key={reel.id}>
        <video src={reel.video_url} poster={reel.thumbnail_url} playsInline controls={false} muted={i !== active} preload={Math.abs(i-active) <= 1 ? 'metadata' : 'none'} />
        {reel.title && <div className="caption">{reel.title}</div>}
      </article>)}
    </section>
  </main>;
}
