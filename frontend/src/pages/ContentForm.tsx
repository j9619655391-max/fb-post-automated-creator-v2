import { useEffect, useState } from 'react';

const BUSINESS_OBJECTIVES = [
  { value: 'product-showcase', label: 'Product showcase', guidance: 'Show a specific suit, garment, fabric, cut, embroidery, or design detail and invite an inquiry.' },
  { value: 'collection-launch', label: 'Collection launch', guidance: 'Introduce a new collection or seasonal line with a clear fashion-led story and booking CTA.' },
  { value: 'bridal-occasion', label: 'Bridal & occasion wear', guidance: 'Highlight bridal, partywear, ceremony, or event styling with consultation and custom-order intent.' },
  { value: 'styling-tips', label: 'Styling advice', guidance: 'Give a practical styling idea connected to suits, fabrics, colors, fit, or accessories.' },
  { value: 'fabric-craft', label: 'Fabric & craftsmanship', guidance: 'Explain fabric quality, tailoring, finishing, embroidery, or the craft behind the design.' },
  { value: 'customer-story', label: 'Customer proof', guidance: 'Use an approved customer experience or testimonial angle without inventing a claim.' },
  { value: 'offer-booking', label: 'Offer / consultation booking', guidance: 'Drive WhatsApp, phone, website, or in-store consultation inquiries using only configured facts.' },
  { value: 'fashion-quote', label: 'Fashion quote card', guidance: 'Create an aspirational fashion quote tied to personal style, confidence, craftsmanship, or the brand story—not generic life motivation.' },
];

const VISUAL_TEMPLATES = [
  { value: 'fashion-editorial', label: 'Fashion editorial', guidance: 'Premium image-led layout with generous negative space, elegant serif/sans pairing, and a restrained footer.' },
  { value: 'product-catalog', label: 'Product catalog', guidance: 'Product-first layout with name, fabric/design detail, availability or custom-order cue, and contact CTA.' },
  { value: 'quote-card', label: 'Quote card', guidance: 'Large quote hierarchy with quotation mark, highlighted keywords, logo/handle, and website or WhatsApp footer.' },
  { value: 'collection-story', label: 'Collection story', guidance: 'Multi-zone composition for collection name, inspiration, hero image, design detail, and consultation CTA.' },
];
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createContent, updateContent, getContent } from '../api/content';
import { getCategories, generateThemes, type ContentCategory } from '../api/vce';
import { listPages, type MetaPage } from '../api/metaPages';
import { listLinkedInAccounts, type LinkedInAccount } from '../api/platforms';
import { uploadMedia } from '../api/media';
import { optimizeContent } from '../api/ai';
import { generateDraft } from '../api/generation';
import { useOrg } from '../context/OrgContext';

export default function ContentForm() {
  const { isAuthenticated } = useAuth();
  const { currentOrg } = useOrg();
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = id != null;
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatingDraft, setGeneratingDraft] = useState(false);
  const [error, setError] = useState('');
  const [loaded, setLoaded] = useState(!isEdit);
  const [previewDevice, setPreviewDevice] = useState<'mobile' | 'desktop'>('mobile');

  // Automation: category → themes → load into form (new content only)
  const [categories, setCategories] = useState<ContentCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<ContentCategory | null>(null);

  const [businessObjective, setBusinessObjective] = useState('product-showcase');
  const [visualTemplate, setVisualTemplate] = useState('fashion-editorial');
  const [themes, setThemes] = useState<string[]>([]);

  const [themesLoading, setThemesLoading] = useState(false);
  const [themeError, setThemeError] = useState('');

  // Schedule for (new content only): when to publish after approval
  const [scheduleAt, setScheduleAt] = useState('');
  const [schedulePlatform, setSchedulePlatform] = useState<'facebook' | 'instagram' | 'linkedin'>('facebook');
  const [schedulePageId, setSchedulePageId] = useState<number | ''>('');
  const [scheduleLinkedInAccountId, setScheduleLinkedInAccountId] = useState<number | ''>('');
  const [pages, setPages] = useState<MetaPage[]>([]);
  const [linkedinAccounts, setLinkedinAccounts] = useState<LinkedInAccount[]>([]);

  // Media state
  const [mediaId, setMediaId] = useState<number | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // AI Optimization state
  const [optimizing, setOptimizing] = useState(false);
  const [optimizedTitle, setOptimizedTitle] = useState('');
  const [optimizedBody, setOptimizedBody] = useState('');

  useEffect(() => {
    if (!isEdit || !isAuthenticated || !id) return;
    getContent(parseInt(id, 10))
      .then((c) => {
        setTitle(c.title);
        setBody(c.body);
        setMediaId(c.media_id || null);
        // If content has media_id, we should ideally fetch its URL if not provided by response
        // In our case ContentResponse includes media_id, but maybe not the URL yet? 
        // Our backend ContentResponse schema shows media_id: Optional[int].
        setLoaded(true);
      })
      .catch(() => { setError('Content not found'); setLoaded(true); });
  }, [isEdit, isAuthenticated, id]);

  // Load categories and pages when creating new content
  useEffect(() => {
    if (isEdit || !isAuthenticated) return;
    getCategories().then((items) => {

      setCategories(items);
      if (!selectedCategory) {
        setSelectedCategory(items.find((item) => item.slug === 'product-showcase') ?? null);
      }
    }).catch(() => setCategories([]));

    listPages(currentOrg?.id).then(setPages).catch(() => setPages([]));
    listLinkedInAccounts().then(setLinkedinAccounts).catch(() => setLinkedinAccounts([]));
  }, [isEdit, isAuthenticated, currentOrg]);

  // Auto-generate themes when category is selected (new content only)
  useEffect(() => {
    if (isEdit || !isAuthenticated || !selectedCategory) {
      setThemes([]);
      return;
    }
    setThemeError('');
    setThemesLoading(true);
    const objective = BUSINESS_OBJECTIVES.find((item) => item.value === businessObjective);

    const template = VISUAL_TEMPLATES.find((item) => item.value === visualTemplate);
    generateThemes({
      category_id: selectedCategory.id,
      count: 8,
      organization_id: currentOrg?.id,
      extra_instruction: `Business objective: ${objective?.guidance ?? businessObjective}. Visual template: ${template?.guidance ?? visualTemplate}.`,
    })

      .then((res) => {
        if (res.available && res.themes.length) setThemes(res.themes);
        else if (!res.available) setThemeError('Theme generation not configured (add GEMINI_API_KEY).');
        else setThemes([]);
      })
      .catch(() => setThemeError('Could not generate themes.'))
      .finally(() => setThemesLoading(false));
  }, [isEdit, isAuthenticated, selectedCategory?.id, businessObjective, visualTemplate, currentOrg?.id]);

  function loadThemeIntoForm(theme: string) {
    setTitle(theme);
    setBody(`Expand on: ${theme}\n\n`);
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');
    try {
      const res = await uploadMedia(file, currentOrg?.id);
      setMediaId(res.id);
      setMediaUrl(res.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  async function handleGenerateDraft() {
    if (isEdit) return;
    setGeneratingDraft(true);
    setError('');
    try {
      const objective = BUSINESS_OBJECTIVES.find((item) => item.value === businessObjective);

      const template = VISUAL_TEMPLATES.find((item) => item.value === visualTemplate);
      const generated = await generateDraft({
        category_id: selectedCategory?.id,
        category_name: selectedCategory?.name,
        organization_id: currentOrg?.id,
        extra_instruction: `Business objective: ${objective?.guidance ?? businessObjective}. Visual template: ${template?.guidance ?? visualTemplate}. Never default to generic motivational content unless the objective explicitly asks for a fashion quote.`,
      });

      navigate(`/content/${generated.id}/edit`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate a draft');
    } finally {
      setGeneratingDraft(false);
    }
  }

  async function handleOptimize() {
    if (!title && !body) {
      setError('Please provide a title or body to optimize.');
      return;
    }
    setOptimizing(true);
    setError('');
    setOptimizedTitle('');
    setOptimizedBody('');
    try {
      const res = await optimizeContent({ title, body });
      setOptimizedTitle(res.optimized_title);
      setOptimizedBody(res.optimized_body);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  }

  function applyOptimization() {
    if (optimizedTitle) setTitle(optimizedTitle);
    if (optimizedBody) setBody(optimizedBody);
    setOptimizedTitle('');
    setOptimizedBody('');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isAuthenticated) return;
    setError('');
    setLoading(true);
    try {
      if (isEdit && id) {
        await updateContent(parseInt(id, 10), { title, body, media_id: mediaId });
        navigate(`/content/${id}`, { replace: true });
      } else {
        const payload: {
          title: string;
          body: string;
          schedule_at?: string;
          schedule_platform?: 'facebook' | 'instagram' | 'linkedin';
          schedule_meta_page_id?: number;
          schedule_linkedin_account_id?: number;
          media_id?: number | null;
          organization_id?: number;
        } = {
          title,
          body,
          media_id: mediaId,
          organization_id: currentOrg?.id
        };
        if (scheduleAt) {
          if (schedulePlatform === 'linkedin' && scheduleLinkedInAccountId !== '') {
            payload.schedule_at = new Date(scheduleAt).toISOString();
            payload.schedule_platform = 'linkedin';
            payload.schedule_linkedin_account_id = scheduleLinkedInAccountId;
          } else if (schedulePlatform !== 'linkedin' && schedulePageId !== '') {
            payload.schedule_at = new Date(scheduleAt).toISOString();
            payload.schedule_platform = schedulePlatform;
            payload.schedule_meta_page_id = schedulePageId;
          }
        }
        const created = await createContent(payload);
        navigate(`/content/${created.id}`, { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setLoading(false);
    }
  }

  if (isEdit && !loaded && !error) {
    return <p className="text-slate-500">Loading...</p>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Left Column: Form */}
        <div className="flex-1">
          <h1 className="text-2xl font-semibold text-slate-900 mb-6">{isEdit ? 'Edit content' : 'New content'}</h1>
          {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

          {/* Automation: Category → AI themes → load into form (new content only) */}
          {!isEdit && (
            <div className="mb-8 p-5 rounded-xl bg-indigo-50 border-2 border-indigo-200">
              <h2 className="text-base font-semibold text-indigo-900 mb-1">Create with AI</h2>
              <p className="text-sm text-indigo-700 mb-3">Generate a complete draft for review, or select a theme and write the post yourself.</p>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                value={selectedCategory?.id ?? ''}
                onChange={(e) => {
                  const id = e.target.value ? parseInt(e.target.value, 10) : 0;
                  setSelectedCategory(categories.find((c) => c.id === id) ?? null);
                }}
                className="mb-3 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Choose category...</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
                            {categories.length === 0 && !themesLoading && <p className="text-slate-500 text-sm mb-2">No categories yet. Restart the local app once to seed business-aware fashion categories.</p>}
              <div className="grid md:grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Business objective</label>
                  <select
                    value={businessObjective}
                    onChange={(e) => setBusinessObjective(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white text-sm"
                  >
                    {BUSINESS_OBJECTIVES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                  <p className="text-xs text-slate-500 mt-1">{BUSINESS_OBJECTIVES.find((item) => item.value === businessObjective)?.guidance}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Creative template family</label>
                  <select
                    value={visualTemplate}
                    onChange={(e) => setVisualTemplate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white text-sm"
                  >
                    {VISUAL_TEMPLATES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                  <p className="text-xs text-slate-500 mt-1">{VISUAL_TEMPLATES.find((item) => item.value === visualTemplate)?.guidance}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mb-3">

                <button
                  type="button"
                  onClick={handleGenerateDraft}
                  disabled={generatingDraft || !isAuthenticated}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {generatingDraft ? 'Generating draft...' : 'Generate business draft'}

                </button>
              </div>
              {themesLoading && <p className="text-indigo-600 text-sm font-medium mb-2">Generating themes...</p>}
              {themeError && <p className="text-amber-700 text-sm mb-2">{themeError}</p>}
              {!themesLoading && themes.length > 0 && (
                <>
                  <p className="text-sm font-medium text-slate-700 mb-2">Click a theme to load it into Title & Body below</p>
                  <div className="flex flex-wrap gap-2">
                    {themes.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => loadThemeIntoForm(t)}
                        className="rounded-lg border-2 border-indigo-300 bg-white px-3 py-2 text-left text-sm text-slate-800 hover:bg-indigo-100 hover:border-indigo-500"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isEdit && (
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Schedule for (optional)</h3>
                <p className="text-xs text-slate-600">After approval, this content will be published to the selected page at the chosen time.</p>
                <div className="flex flex-wrap gap-4 items-end">
                  <div>
                    <label htmlFor="schedule_platform" className="block text-xs font-medium text-slate-600 mb-1">Platform</label>
                    <select
                      id="schedule_platform"
                      value={schedulePlatform}
                      onChange={(e) => {
                        const platform = e.target.value as 'facebook' | 'instagram' | 'linkedin';
                        setSchedulePlatform(platform);
                        setSchedulePageId('');
                        setScheduleLinkedInAccountId('');
                      }}
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="facebook">Facebook</option>
                      <option value="instagram">Instagram</option>
                      <option value="linkedin">LinkedIn</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="schedule_at" className="block text-xs font-medium text-slate-600 mb-1">Date & time</label>
                    <input
                      id="schedule_at"
                      type="datetime-local"
                      value={scheduleAt}
                      onChange={(e) => setScheduleAt(e.target.value)}
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="schedule_target" className="block text-xs font-medium text-slate-600 mb-1">
                      {schedulePlatform === 'linkedin' ? 'Publish to account' : schedulePlatform === 'instagram' ? 'Publish to Meta page / Instagram' : 'Publish to page'}
                    </label>
                    {schedulePlatform === 'linkedin' ? (
                      <select
                        id="schedule_target"
                        value={scheduleLinkedInAccountId === '' ? '' : scheduleLinkedInAccountId}
                        onChange={(e) => setScheduleLinkedInAccountId(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[220px]"
                      >
                        <option value="">Select LinkedIn account...</option>
                        {linkedinAccounts.map((account) => (
                          <option key={account.id} value={account.id}>{account.name} ({account.account_type})</option>
                        ))}
                      </select>
                    ) : (
                      <select
                        id="schedule_target"
                        value={schedulePageId === '' ? '' : schedulePageId}
                        onChange={(e) => setSchedulePageId(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[220px]"
                      >
                        <option value="">Select page...</option>
                        {pages.map((p) => (
                          <option key={p.id} value={p.id}>{p.page_name || p.page_id}</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <label htmlFor="title" className="block text-sm font-medium text-slate-700">Title</label>
              <button
                type="button"
                onClick={handleOptimize}
                disabled={optimizing || (!title && !body)}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 disabled:opacity-50 flex items-center gap-1"
              >
                {optimizing ? 'Optimizing...' : 'AI Enhance ✨'}
              </button>
            </div>
            <div>
              <input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={200}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="body" className="block text-sm font-medium text-slate-700 mb-1">Body</label>
              <textarea
                id="body"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                required
                rows={6}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {(optimizedTitle || optimizedBody) && (
              <div className="p-4 rounded-xl bg-indigo-50 border-2 border-indigo-200 shadow-sm relative overflow-hidden group">
                <div className="absolute -right-4 -top-4 w-20 h-20 bg-indigo-200/30 rounded-full blur-xl group-hover:bg-indigo-300/40 transition-all duration-700"></div>
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <h3 className="text-sm font-bold text-indigo-900 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-indigo-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                    AI Suggested Optimization
                  </h3>
                  <button
                    type="button"
                    onClick={() => { setOptimizedTitle(''); setOptimizedBody(''); }}
                    className="text-indigo-400 hover:text-indigo-600 p-1"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <div className="space-y-3 relative z-10">
                  {optimizedTitle && (
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-0.5 block">Suggested Title</span>
                      <p className="text-sm font-medium text-indigo-950 bg-white/60 p-2 rounded border border-indigo-100/50">{optimizedTitle}</p>
                    </div>
                  )}
                  {optimizedBody && (
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-0.5 block">Suggested Body</span>
                      <p className="text-sm text-indigo-900 bg-white/60 p-2 rounded border border-indigo-100/50 whitespace-pre-wrap">{optimizedBody}</p>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={applyOptimization}
                    className="mt-2 w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-indigo-700 transition-colors"
                  >
                    Apply Changes to Draft
                  </button>
                </div>
              </div>
            )}

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
              <label className="block text-sm font-medium text-slate-700">Attach Media (Image or Video)</label>
              <div className="flex items-center gap-4">
                <input
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileChange}
                  className="hidden"
                  id="media-upload"
                  disabled={uploading}
                />
                <label
                  htmlFor="media-upload"
                  className={`cursor-pointer rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 ${uploading ? 'opacity-50' : ''}`}
                >
                  {uploading ? 'Uploading...' : 'Choose File'}
                </label>
                {mediaId && <span className="text-xs text-green-600 font-medium">File attached</span>}
              </div>
              {mediaUrl && (
                <div className="mt-2 relative w-full max-w-sm rounded-lg overflow-hidden border border-slate-300 aspect-video bg-slate-200">
                  {mediaUrl.match(/\.(mp4|webm|ogg)$/) ? (
                    <video src={mediaUrl} controls className="w-full h-full object-contain" />
                  ) : (
                    <img src={mediaUrl} alt="Preview" className="w-full h-full object-contain" />
                  )}
                  <button
                    type="button"
                    onClick={() => { setMediaId(null); setMediaUrl(null); }}
                    className="absolute top-2 right-2 p-1 bg-red-600 text-white rounded-full hover:bg-red-700"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-slate-900 text-white px-4 py-2 font-medium hover:bg-slate-800 disabled:opacity-50"
              >
                {loading ? 'Saving...' : isEdit ? 'Save' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Live Facebook Preview */}
        <div className="lg:w-[450px] flex-shrink-0">
          <div className="sticky top-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-slate-500 uppercase tracking-widest">Post Preview</h2>
              <div className="flex bg-slate-100 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setPreviewDevice('mobile')}
                  className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${previewDevice === 'mobile' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  MOBILE
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewDevice('desktop')}
                  className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${previewDevice === 'desktop' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  DESKTOP
                </button>
              </div>
            </div>

            <div className={`transition-all duration-300 mx-auto ${previewDevice === 'mobile' ? 'max-w-[360px]' : 'w-full'}`}>
              <div className="bg-white rounded-xl shadow-2xl shadow-indigo-100 border border-slate-200 overflow-hidden font-sans ring-1 ring-slate-900/5">
                {/* FB Header */}
                <div className="p-3 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-200 flex-shrink-0 border border-slate-100 flex items-center justify-center overflow-hidden shadow-inner">
                    <svg className="w-6 h-6 text-slate-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" /></svg>
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-900 leading-tight">
                      {schedulePlatform === 'linkedin'
                        ? (scheduleLinkedInAccountId ? linkedinAccounts.find((account) => account.id === scheduleLinkedInAccountId)?.name : 'LinkedIn Account')
                        : (schedulePageId ? pages.find(p => p.id === schedulePageId)?.page_name : 'Drafting Page')}
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                      Sponsored · <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 16 16"><path d="M8 0a8 8 0 1 0 8 8A8 8 0 0 0 8 0zM4.5 7.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5z" /></svg>
                    </div>
                  </div>
                </div>

                {/* FB Body */}
                <div className="px-3 pb-4">
                  {title && <div className="text-[15px] font-bold text-slate-900 mb-1.5 leading-snug">{title}</div>}
                  <div className="text-[14px] text-slate-900 whitespace-pre-wrap leading-normal">{body || 'Your high-engagement masterpiece starts here...'}</div>
                </div>

                {/* FB Media */}
                <div className={`relative bg-slate-50 overflow-hidden ${mediaUrl ? 'border-t border-slate-100' : ''}`}>
                  {mediaUrl ? (
                    mediaUrl.match(/\.(mp4|webm|ogg)$/) ? (
                      <video src={mediaUrl} className="w-full h-auto max-h-[400px] object-cover" controls />
                    ) : (
                      <img src={mediaUrl} alt="Preview" className="w-full h-auto max-h-[400px] object-cover" />
                    )
                  ) : (
                    <div className="h-2 w-full bg-slate-50"></div>
                  )}
                </div>

                {/* FB Action Bar */}
                <div className="px-3 py-2 border-t border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="flex -space-x-1">
                      <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center ring-2 ring-white">
                        <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1v1h1c1 0 2 1 2 2v1c0 1-1 2-2 2H4v1c0 1 1 2 2 2h1c1 0 2-1 2-2V4c0-1-1-2-2-2H4V1z" /></svg>
                      </div>
                      <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center ring-2 ring-white">
                        <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z" /></svg>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-slate-500">1.2K</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-500">
                    <span>48 Comments</span> · <span>12 Shares</span>
                  </div>
                </div>

                <div className="px-1 py-1 flex justify-around border-t border-slate-100 mx-2">
                  <div className="flex-1 flex items-center justify-center gap-2 text-sm font-bold text-slate-500 py-2 hover:bg-slate-50 rounded-lg transition-colors">
                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10h4.708C19.746 10 20.5 10.754 20.5 11.692V14.5c0 .414-.336.75-.75.75H14v4.708c0 .938-.754 1.692-1.692 1.692h-2.808c-.414 0-.75-.336-.75-.75V15.25H4v-4.708c0-.938.754-1.692 1.692-1.692h2.808c.414 0 .75.336.75.75V10h4.708z" /></svg> Like
                  </div>
                  <div className="flex-1 flex items-center justify-center gap-2 text-sm font-bold text-slate-500 py-2 hover:bg-slate-50 rounded-lg transition-colors">
                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg> Comment
                  </div>
                  <div className="flex-1 flex items-center justify-center gap-2 text-sm font-bold text-slate-500 py-2 hover:bg-slate-50 rounded-lg transition-colors">
                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg> Share
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100/50 shadow-sm text-emerald-900 text-[13px] leading-relaxed relative overflow-hidden group">
              <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-emerald-200/20 rounded-full blur-2xl group-hover:bg-emerald-300/30 transition-all duration-700"></div>
              <p className="font-black uppercase tracking-widest text-[10px] text-emerald-600 mb-2">Editor Intelligence</p>
              <p className="font-medium relative z-10">
                Your post will be published exactly as shown in this preview. Use <span className="text-indigo-600 font-bold">"Create with AI"</span> to generate high-engagement hooks and formatting optimized for Meta's algorithm.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
