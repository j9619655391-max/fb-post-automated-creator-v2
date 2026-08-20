import { useEffect, useMemo, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import {
  addWorkspaceSource,
  getWorkspaceIntelligence,
  refreshWorkspaceSource,
  refreshWorkspaceSources,
  removeWorkspaceSource,
  saveWorkspaceProfile,
  type WorkspaceIntelligence,
  type WorkspaceProfileInput,
  type WorkspaceSourceType,
} from '../api/workspaceIntelligence';

const emptyProfile: WorkspaceProfileInput = {
  business_description: '',
  mission: '',
  industry: '',
  services: [],
  products: [],
  target_audience: '',
  locations: [],
  brand_voice: '',
  tone: '',
  keywords: [],
  preferred_languages: ['English'],
  contact_email: '',
  contact_phone: '',
  whatsapp_display_phone: '',
  whatsapp_business_account_id: '',
  website_url: '',
  linkedin_url: '',
  facebook_url: '',
  instagram_url: '',
  whatsapp_url: '',
  approved_claims: [],
  prohibited_claims: [],
};

function listValue(items: string[]) {
  return items.join(', ');
}

function parseList(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean).slice(0, 100);
}

function profileToForm(intelligence: WorkspaceIntelligence): WorkspaceProfileInput {
  if (!intelligence.profile) return emptyProfile;
  const profile = intelligence.profile;
  return {
    business_description: profile.business_description || '',
    mission: profile.mission || '',
    industry: profile.industry || '',
    services: profile.services || [],
    products: profile.products || [],
    target_audience: profile.target_audience || '',
    locations: profile.locations || [],
    brand_voice: profile.brand_voice || '',
    tone: profile.tone || '',
    keywords: profile.keywords || [],
    preferred_languages: profile.preferred_languages || [],
    contact_email: profile.contact_email || '',
    contact_phone: profile.contact_phone || '',
    whatsapp_display_phone: profile.whatsapp_display_phone || '',
    whatsapp_business_account_id: profile.whatsapp_business_account_id || '',
    website_url: profile.website_url || '',
    linkedin_url: profile.linkedin_url || '',
    facebook_url: profile.facebook_url || '',
    instagram_url: profile.instagram_url || '',
    whatsapp_url: profile.whatsapp_url || '',
    approved_claims: profile.approved_claims || [],
    prohibited_claims: profile.prohibited_claims || [],
  };
}

export default function WorkspaceIntelligence() {
  const { currentOrg } = useOrg();
  const [intelligence, setIntelligence] = useState<WorkspaceIntelligence | null>(null);
  const [form, setForm] = useState<WorkspaceProfileInput>(emptyProfile);
  const [sourceType, setSourceType] = useState<WorkspaceSourceType>('website');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceTitle, setSourceTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const sourceSummary = useMemo(() => {
    if (!intelligence) return 'No sources yet';
    return `${intelligence.source_count} source${intelligence.source_count === 1 ? '' : 's'} · ${intelligence.approved_source_count} approved`;
  }, [intelligence]);

  useEffect(() => {
    if (!currentOrg) {
      setIntelligence(null);
      setForm(emptyProfile);
      return;
    }
    setLoading(true);
    setError('');
    getWorkspaceIntelligence(currentOrg.id)
      .then((data) => {
        setIntelligence(data);
        setForm(profileToForm(data));
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load workspace intelligence'))
      .finally(() => setLoading(false));
  }, [currentOrg?.id]);

  function updateField<K extends keyof WorkspaceProfileInput>(field: K, value: WorkspaceProfileInput[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!currentOrg) return;
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const saved = await saveWorkspaceProfile(currentOrg.id, form);
      setForm(profileToForm({ profile: saved, sources: intelligence?.sources || [], source_count: intelligence?.source_count || 0, approved_source_count: intelligence?.approved_source_count || 0 }));
      setMessage('Workspace intelligence profile saved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save workspace profile');
    } finally {
      setSaving(false);
    }
  }

  async function handleAddSource(e: React.FormEvent) {
    e.preventDefault();
    if (!currentOrg) return;
    if (sourceType === 'website' && !sourceUrl.trim()) {
      setError('A public website URL is required.');
      return;
    }
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const source = await addWorkspaceSource(currentOrg.id, {
        source_type: sourceType,
        url: sourceUrl.trim() || undefined,
        title: sourceTitle.trim() || undefined,
        provider: sourceType === 'manual' ? undefined : sourceType.split('_')[0],
      });
      setIntelligence((current) => current ? { ...current, sources: [source, ...current.sources], source_count: current.source_count + 1 } : current);
      setSourceUrl('');
      setSourceTitle('');
      setMessage('Source added. Refresh it to collect the latest public information.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add source');
    } finally {
      setSaving(false);
    }
  }

  async function handleRefreshAll() {
    if (!currentOrg) return;
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const result = await refreshWorkspaceSources(currentOrg.id);
      const data = await getWorkspaceIntelligence(currentOrg.id);
      setIntelligence(data);
      setMessage(`${result.refreshed_count} website source${result.refreshed_count === 1 ? '' : 's'} refreshed.${result.errors.length ? ` ${result.errors.length} source(s) need review.` : ''}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not refresh sources');
    } finally {
      setSaving(false);
    }
  }

  async function handleRefreshSource(sourceId: number) {
    if (!currentOrg) return;
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const refreshed = await refreshWorkspaceSource(currentOrg.id, sourceId);
      setIntelligence((current) => current ? { ...current, sources: current.sources.map((source) => source.id === sourceId ? refreshed : source) } : current);
      setMessage('Source refreshed and marked pending review.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not refresh source');
    } finally {
      setSaving(false);
    }
  }

  async function handleRemoveSource(sourceId: number) {
    if (!currentOrg || !window.confirm('Remove this source from the workspace knowledge base?')) return;
    setSaving(true);
    setMessage('');
    setError('');
    try {
      await removeWorkspaceSource(currentOrg.id, sourceId);
      setIntelligence((current) => current ? { ...current, sources: current.sources.filter((source) => source.id !== sourceId), source_count: Math.max(0, current.source_count - 1) } : current);
      setMessage('Source removed.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove source');
    } finally {
      setSaving(false);
    }
  }

  if (!currentOrg) {
    return <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">Select a workspace to manage its business intelligence profile.</div>;
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-indigo-600">Workspace knowledge</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900">{currentOrg.name} Intelligence</h1>
          <p className="mt-2 max-w-3xl text-slate-600">Keep verified business facts, public sources, social links, and approved claims in one place. AI drafts will use this context instead of guessing.</p>
        </div>
        <button type="button" onClick={handleRefreshAll} disabled={saving || loading} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Working...' : 'Refresh website sources'}</button>
      </header>

      {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <form onSubmit={handleSaveProfile} className="space-y-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5"><h2 className="text-xl font-bold text-slate-900">Business foundation</h2><p className="mt-1 text-sm text-slate-500">These facts become the primary context for content generation and marketing recommendations.</p></div>
          <div className="grid gap-5 md:grid-cols-2">
            <label className="md:col-span-2 text-sm font-semibold text-slate-700">Business description<textarea value={form.business_description || ''} onChange={(e) => updateField('business_description', e.target.value)} rows={4} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="What does this business do, for whom, and why does it matter?" /></label>
            <label className="text-sm font-semibold text-slate-700">Industry<input value={form.industry || ''} onChange={(e) => updateField('industry', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="Digital marketing" /></label>
            <label className="text-sm font-semibold text-slate-700">Tone<input value={form.tone || ''} onChange={(e) => updateField('tone', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="Professional, practical, optimistic" /></label>
            <label className="text-sm font-semibold text-slate-700">Mission<textarea value={form.mission || ''} onChange={(e) => updateField('mission', e.target.value)} rows={3} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">Target audience<textarea value={form.target_audience || ''} onChange={(e) => updateField('target_audience', e.target.value)} rows={3} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="Who should the content reach?" /></label>
            <label className="text-sm font-semibold text-slate-700">Services <span className="font-normal text-slate-400">comma separated</span><input value={listValue(form.services)} onChange={(e) => updateField('services', parseList(e.target.value))} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">Products/offers <span className="font-normal text-slate-400">comma separated</span><input value={listValue(form.products)} onChange={(e) => updateField('products', parseList(e.target.value))} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">Locations <span className="font-normal text-slate-400">comma separated</span><input value={listValue(form.locations)} onChange={(e) => updateField('locations', parseList(e.target.value))} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">Keywords <span className="font-normal text-slate-400">comma separated</span><input value={listValue(form.keywords)} onChange={(e) => updateField('keywords', parseList(e.target.value))} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="md:col-span-2 text-sm font-semibold text-slate-700">Brand voice guidance<textarea value={form.brand_voice || ''} onChange={(e) => updateField('brand_voice', e.target.value)} rows={3} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="Words to use, words to avoid, writing style, cultural context, and examples." /></label>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5"><h2 className="text-xl font-bold text-slate-900">Official links and contact channels</h2><p className="mt-1 text-sm text-slate-500">Use public business URLs or authorized business accounts. Personal/private profiles are not collected.</p></div>
          <div className="grid gap-5 md:grid-cols-2">
            {([['website_url', 'Website'], ['linkedin_url', 'LinkedIn Page/Profile'], ['facebook_url', 'Facebook Page'], ['instagram_url', 'Instagram Business/Creator'], ['whatsapp_url', 'WhatsApp Business link']] as const).map(([field, label]) => (
              <label key={field} className="text-sm font-semibold text-slate-700">{label}<input type="url" value={String(form[field] || '')} onChange={(e) => updateField(field, e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="https://" /></label>
            ))}
            <label className="text-sm font-semibold text-slate-700">Contact email<input type="email" value={form.contact_email || ''} onChange={(e) => updateField('contact_email', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">Contact phone<input value={form.contact_phone || ''} onChange={(e) => updateField('contact_phone', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">WhatsApp display phone<input value={form.whatsapp_display_phone || ''} onChange={(e) => updateField('whatsapp_display_phone', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" /></label>
            <label className="text-sm font-semibold text-slate-700">WhatsApp Business Account ID<input value={form.whatsapp_business_account_id || ''} onChange={(e) => updateField('whatsapp_business_account_id', e.target.value)} className="mt-1 w-full rounded-xl border-slate-300 text-sm" placeholder="Only if authorized" /></label>
          </div>
        </section>

        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <h2 className="text-xl font-bold text-amber-950">Claim controls</h2>
          <p className="mt-1 text-sm text-amber-800">Approved claims can be used in posts. Prohibited claims will be treated as hard editorial restrictions.</p>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <label className="text-sm font-semibold text-amber-950">Approved claims <span className="font-normal text-amber-700">comma separated</span><textarea value={listValue(form.approved_claims)} onChange={(e) => updateField('approved_claims', parseList(e.target.value))} rows={4} className="mt-1 w-full rounded-xl border-amber-300 text-sm" placeholder="Only claims supported by your business" /></label>
            <label className="text-sm font-semibold text-amber-950">Prohibited claims <span className="font-normal text-amber-700">comma separated</span><textarea value={listValue(form.prohibited_claims)} onChange={(e) => updateField('prohibited_claims', parseList(e.target.value))} rows={4} className="mt-1 w-full rounded-xl border-amber-300 text-sm" placeholder="Claims or topics the AI must never make" /></label>
          </div>
        </section>

        <button type="submit" disabled={saving || loading} className="rounded-xl bg-slate-900 px-6 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-50">{saving ? 'Saving...' : 'Save workspace intelligence'}</button>
      </form>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><h2 className="text-xl font-bold text-slate-900">Knowledge sources</h2><p className="mt-1 text-sm text-slate-500">{sourceSummary}. Website sources are fetched only when you request a refresh and are marked pending review.</p></div></div>
        <form onSubmit={handleAddSource} className="mt-5 grid gap-3 md:grid-cols-[180px_1fr_1fr_auto]">
          <select value={sourceType} onChange={(e) => setSourceType(e.target.value as WorkspaceSourceType)} className="rounded-xl border-slate-300 text-sm"><option value="website">Website</option><option value="facebook_page">Facebook Page</option><option value="instagram_account">Instagram Business</option><option value="linkedin_page">LinkedIn Page</option><option value="whatsapp_business">WhatsApp Business</option><option value="manual">Manual source</option></select>
          <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} type="url" placeholder="https://business.example.com" className="rounded-xl border-slate-300 text-sm" />
          <input value={sourceTitle} onChange={(e) => setSourceTitle(e.target.value)} placeholder="Source title (optional)" className="rounded-xl border-slate-300 text-sm" />
          <button type="submit" disabled={saving} className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50">Add source</button>
        </form>
        <div className="mt-6 space-y-3">
          {loading && <p className="text-sm text-slate-500">Loading workspace sources...</p>}
          {!loading && intelligence?.sources.length === 0 && <p className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">Add a website or authorized social source to start building verified context.</p>}
          {intelligence?.sources.map((source) => (
            <div key={source.id} className="rounded-xl border border-slate-200 p-4"><div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-indigo-50 px-2 py-1 text-[10px] font-black uppercase tracking-wider text-indigo-700">{source.source_type.replace('_', ' ')}</span><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold uppercase text-slate-600">{source.review_status}</span></div><h3 className="mt-2 font-semibold text-slate-900">{source.title || source.url || 'Manual source'}</h3><p className="mt-1 break-all text-xs text-slate-500">{source.url || source.excerpt || 'No URL; add content through the source API.'}</p>{source.last_fetched_at && <p className="mt-2 text-xs text-slate-400">Last fetched {new Date(source.last_fetched_at).toLocaleString()}</p>}</div><div className="flex shrink-0 gap-2"><button type="button" disabled={saving || source.source_type !== 'website'} onClick={() => handleRefreshSource(source.id)} className="rounded-lg border border-indigo-200 px-3 py-2 text-xs font-bold text-indigo-700 disabled:cursor-not-allowed disabled:opacity-40">Refresh</button><button type="button" disabled={saving} onClick={() => handleRemoveSource(source.id)} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-bold text-red-600 disabled:opacity-40">Remove</button></div></div>{source.excerpt && <p className="mt-3 line-clamp-3 text-sm text-slate-600">{source.excerpt}</p>}</div>
          ))}
        </div>
      </section>
    </div>
  );
}
