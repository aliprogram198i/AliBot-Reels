import { useEffect, useMemo, useRef, useState } from 'react';
import './styles.css';

type Category = { id: string; label: string; emoji: string; restricted?: boolean };
type Reel = { id: string; category: string; video_url: string; thumbnail_url?: string; title?: string };
type Me = { authenticated: boolean; user: { name?: string; email?: string; picture?: string; age_eligible: boolean } | null };
type TelegramApi = { WebApp?: { initData?: string; ready: () => void; expand: () => void } };

const countries = [
  ['NL','🇳🇱','هولندا'],['DE','🇩🇪','ألمانيا'],['FR','🇫🇷','فرنسا'],['GB','🇬🇧','بريطانيا'],
  ['US','🇺🇸','الولايات المتحدة'],['CA','🇨🇦','كندا'],['TR','🇹🇷','تركيا'],['SA','🇸🇦','السعودية'],
  ['AE','🇦🇪','الإمارات'],['EG','🇪🇬','مصر'],['IQ','🇮🇶','العراق'],['JO','🇯🇴','الأردن'],
  ['MA','🇲🇦','المغرب'],['DZ','🇩🇿','الجزائر'],['TN','🇹🇳','تونس'],['ES','🇪🇸','إسبانيا'],
  ['IT','🇮🇹','إيطاليا'],['SE','🇸🇪','السويد'],['NO','🇳🇴','النرويج'],['AU','🇦🇺','أستراليا'],
] as const;

type Category = { id: string; label: string; emoji: string; restricted?: boolean };
type Reel = { id: string; category: string; video_url: string; thumbnail_url?: string; title?: string };
type Me = { authenticated: boolean; user: { name?: string; email?: string; picture?: string; age_eligible: boolean } | null };
type TelegramApi = { WebApp?: { initData?: string; ready: () => void; expand: () => void } };

const categories: Category[] = [
  { id: 'all', label: 'الكل', emoji: '🔥' }, { id: 'sports', label: 'رياضة', emoji: '⚽' },
  { id: 'gaming', label: 'ألعاب', emoji: '🎮' }, { id: 'music', label: 'موسيقى', emoji: '🎵' },
  { id: 'entertainment', label: 'ترفيه', emoji: '😂' }, { id: 'kids', label: 'أطفال', emoji: '👶' },
  { id: 'food', label: 'طبخ', emoji: '🍳' }, { id: 'animals', label: 'حيوانات', emoji: '🐾' },
  { id: 'travel', label: 'سفر', emoji: '✈️' }, { id: 'fitness', label: 'لياقة', emoji: '💪' },
  { id: 'adult', label: 'بالغين', emoji: '🔞', restricted: true },
];

const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function App() {
  const [step, setStep] = useState<'countries'|'category'|'feed'>('countries');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [category, setCategory] = useState('all');
  const [reels, setReels] = useState<Reel[]>([]);
  const [active, setActive] = useState(0);
  const [me, setMe] = useState<Me>({ authenticated: false, user: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const videos = useRef<Array<HTMLVideoElement | null>>([]);

  useEffect(() => {
    const telegram = (window as Window & { Telegram?: TelegramApi }).Telegram?.WebApp;
    telegram?.ready(); telegram?.expand();
    const authenticate = async () => {
      if (telegram?.initData) {
        const response = await fetch(API + '/api/auth/telegram', { method:'POST', headers:{'Content-Type':'application/json'}, credentials:'include', body:JSON.stringify({init_data:telegram.initData}) });
        if (response.ok) { const current=await fetch(API+'/api/me',{credentials:'include'}); if(current.ok) setMe(await current.json()); return; }
      }
      const current=await fetch(API+'/api/me',{credentials:'include'}); if(current.ok) setMe(await current.json());
    };
    void authenticate();
  }, []);

  const loadFeed = async (nextCategory = category) => {
    setLoading(true); setError(''); setActive(0); setReels([]);
    try {
      const r=await fetch(API+'/api/feed?category='+encodeURIComponent(nextCategory),{credentials:'include'});
      if(r.status===403) throw new Error('AGE_REQUIRED');
      if(!r.ok) throw new Error('FEED');
      const data=await r.json(); setReels(Array.isArray(data.items)?data.items:[]);
    } catch(e) { setError(e instanceof Error && e.message==='AGE_REQUIRED'?'AGE_REQUIRED':'FEED'); }
    finally { setLoading(false); }
  };

  const completeCountries = () => { if(selectedCountries.length===0){setError('COUNTRIES_REQUIRED');return;} setError(''); setStep('category'); };
  const completeCategory = async (c: Category) => {
    if(c.restricted && !me.user?.age_eligible){setError('AGE_REQUIRED');return;}
    setCategory(c.id);
    if(me.authenticated){
      await fetch(API+'/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({countries:selectedCountries,category:c.id})});
    }
    setStep('feed'); await loadFeed(c.id);
  };
  const login=()=>{window.location.href=API+'/api/auth/google/login';};
  const selectCountry=(code:string)=>setSelectedCountries(x=>x.includes(code)?x.filter(v=>v!==code):[...x,code]);

  useEffect(()=> {
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting&&entry.intersectionRatio>=.65){const i=Number((entry.target as HTMLElement).dataset.index);if(Number.isFinite(i))setActive(i);}}),{threshold:[.65]});
    videos.current.forEach(v=>v&&observer.observe(v)); return()=>observer.disconnect();
  },[reels]);
  useEffect(()=>{videos.current.forEach((v,i)=>{if(!v)return;if(i===active){v.muted=true;void v.play().catch(()=>undefined);}else{v.pause();v.currentTime=0;}})},[active,reels]);

  if(step!=='feed') return <main className="onboarding">
    <section className="onboarding-card">
      <div className="brand">AliBot Reels</div>
      {step==='countries' ? <>
        <span className="step">الخطوة 1 من 2</span>
        <h1>من أي بلدان تريد مشاهدة المحتوى؟</h1>
        <p>اختر بلداً واحداً أو عدة بلدان. سنستخدم اختيارك لتخصيص الـFeed.</p>
        <div className="country-grid">{countries.map(([code,flag,label])=><button key={code} className={selectedCountries.includes(code)?'country selected':'country'} onClick={()=>selectCountry(code)}><span>{flag}</span><b>{label}</b>{selectedCountries.includes(code)&&<i>✓</i>}</button>)}</div>
        {error==='COUNTRIES_REQUIRED'&&<div className="notice">اختر بلداً واحداً على الأقل.</div>}
        <button className="continue" disabled={!selectedCountries.length} onClick={completeCountries}>متابعة <span>←</span></button>
      </> : <>
        <span className="step">الخطوة 2 من 2</span>
        <h1>ما نوع المحتوى الذي تفضله؟</h1>
        <p>اختر الفئة، ويمكنك تغييرها لاحقاً من داخل التطبيق.</p>
        <div className="category-grid">{categories.map(c=><button key={c.id} className="choice" onClick={()=>completeCategory(c)}>{c.emoji}<b>{c.label}</b></button>)}</div>
        {error==='AGE_REQUIRED'&&<div className="notice">هذه الفئة تتطلب تسجيل الدخول وتأكيد الأهلية العمرية.</div>}
        <button className="back" onClick={()=>setStep('countries')}>→ العودة لاختيار البلدان</button>
      </>}
    </section>
  </main>;

  return <main className="app-shell">
    <header className="topbar"><strong>AliBot Reels</strong><button className="login" onClick={login}>{me.authenticated?(me.user?.name||'حسابي'):'تسجيل Google'}</button></header>
    <nav className="categories">{categories.map(c=><button key={c.id} className={category===c.id?'cat active':'cat'} onClick={()=>completeCategory(c)}>{c.emoji} {c.label}</button>)}</nav>
    <section className="feed" aria-label="الفيديوهات">
      {loading&&<div className="empty">جارٍ تحميل القائمة…</div>}
      {!loading&&!error&&reels.length===0&&<div className="empty">لا توجد فيديوهات منشورة في هذه الفئة حالياً.</div>}
      {!loading&&error==='FEED'&&<div className="empty">تعذر تحميل القائمة حالياً.</div>}
      {reels.map((reel,i)=><article className="reel" key={reel.id}><video ref={e=>{videos.current[i]=e}} data-index={i} src={reel.video_url} poster={reel.thumbnail_url} playsInline muted controls={false} preload={i===active+1?'metadata':i===active?'auto':'none'}/><div className="shade"/>{reel.title&&<div className="caption">{reel.title}</div>}</article>)}
    </section>
  </main>;
}
