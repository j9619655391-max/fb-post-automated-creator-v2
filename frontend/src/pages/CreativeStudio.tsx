import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import { listMedia, uploadMedia, type Media } from '../api/media';
import { composeCompleteSocialPackage, type CompleteSocialPostPackage, type CompleteSocialPostComposeRequest } from '../api/remainingRoadmap';

const OBJECTIVE_OPTIONS = [
  { value: 'awareness', label: 'Awareness' },
  { value: 'education', label: 'Education' },
  { value: 'product discovery', label: 'Product discovery' },
  { value: 'conversion', label: 'Conversion / inquiry' },
  { value: 'lead generation', label: 'Lead generation' },
  { value: 'proof', label: 'Proof / case study' },
  { value: 'community', label: 'Community / quote' },
] as const;

const TEMPLATE_OPTIONS = [
  { value: 'service-editorial', label: 'Service / solution editorial', description: 'Image-led solution card with a clear capability, benefit, and truthful CTA.' },
  { value: 'product-catalog', label: 'Product / software catalog', description: 'Product-first card with one capability, use case, and inquiry CTA.' },
  { value: 'technology-explainer', label: 'Technology explainer', description: 'Structured visual for a workflow, integration, checklist, or technical insight.' },
  { value: 'collection-story', label: 'Case study / solution story', description: 'Context, approved proof, project detail, and next-step zones.' },
  { value: 'fashion-editorial', label: 'Fashion editorial', description: 'Premium image-led card with an elegant text-safe panel.' },
  { value: 'quote-card', label: 'Quote card', description: 'Large quote, quotation mark, highlighted identity, and footer.' },
] as const;

const BACKGROUND_PRESETS = [
  { value: 'midnight-aurora', label: 'Midnight Aurora', description: 'Deep navy, soft glow, gold accent', swatch: 'linear-gradient(135deg,#111827,#030712 65%,#ec4899)' },
  { value: 'warm-paper', label: 'Warm Paper', description: 'Cream paper, terracotta edge', swatch: 'linear-gradient(135deg,#fff7ed,#fed7aa 58%,#c2410c)' },
  { value: 'rose-editorial', label: 'Rose Editorial', description: 'Plum, rose panel, premium emotion', swatch: 'linear-gradient(135deg,#4a044e,#831843 62%,#f9a8d4)' },
  { value: 'sunset-glow', label: 'Sunset Glow', description: 'Coral, saffron, plum motivation', swatch: 'linear-gradient(135deg,#fb7185,#f59e0b 52%,#581c87)' },
  { value: 'minimal-ink', label: 'Minimal Ink', description: 'Off-white, serif, whitespace', swatch: 'linear-gradient(135deg,#fafaf9,#ffffff 60%,#f59e0b)' },
  { value: 'neon-night', label: 'Neon Night', description: 'Charcoal, cyan, pink geometry', swatch: 'linear-gradient(135deg,#111827,#06b6d4 55%,#ec4899)' },
] as const;

type BackgroundPreset = typeof BACKGROUND_PRESETS[number]['value'];

export default function CreativeStudio() {
  const { currentOrg } = useOrg();
  const [media, setMedia] = useState<Media[]>([]);
  const [sourceMediaId, setSourceMediaId] = useState<number | ''>('');
  const [useBrandedTextCard, setUseBrandedTextCard] = useState(false);
  const [templateFamily, setTemplateFamily] = useState<CompleteSocialPostComposeRequest['template_family']>('service-editorial');
  const [backgroundPreset, setBackgroundPreset] = useState<BackgroundPreset>('midnight-aurora');
  const [objective, setObjective] = useState('awareness');
  const [creativeArchetype, setCreativeArchetype] = useState('service-announcement');
  const [sourceRefs, setSourceRefs] = useState('');
  const [claimRefs, setClaimRefs] = useState('');
  const [sourceRefIds, setSourceRefIds] = useState('');
  const [claimRefIds, setClaimRefIds] = useState('');
  const [confirmComposeOpen, setConfirmComposeOpen] = useState(false);
  const [composeConfirmed, setComposeConfirmed] = useState(false);
  const [headline, setHeadline] = useState('');
  const [body, setBody] = useState('');
  const [caption, setCaption] = useState('');
  const [hashtags, setHashtags] = useState('business, technology, digital');
  const [tags, setTags] = useState('');
  const [cta, setCta] = useState('Message us for a consultation');
  const [website, setWebsite] = useState('');
  const [handle, setHandle] = useState('');
  const [phone, setPhone] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [location, setLocation] = useState('');
  const [results, setResults] = useState<CompleteSocialPostPackage[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const isQuoteWorkspace = Boolean(currentOrg && /love|truth|motivational|pain|quote/i.test(currentOrg.name));

  useEffect(() => {
    if (isQuoteWorkspace) {
      setTemplateFamily('quote-card');
      setCreativeArchetype('quote-card');
      setObjective('community');
      setUseBrandedTextCard(true);
      setBackgroundPreset('rose-editorial');
      setHashtags('hinglishquotes, lovetruthmotivationpain, dilkibaat');
      setCta('Agar dil ko laga, share karo.');
    }
  }, [currentOrg?.id, isQuoteWorkspace]);

  useEffect(() => {
    if (!currentOrg) return;
    listMedia()
      .then((items) => {
        const images = items.filter((item) => item.mime_type.startsWith('image/'));
        setMedia(images);
        if (images.length && sourceMediaId === '') setSourceMediaId(images[0].id);
      })
      .catch(() => setMedia([]));
  }, [currentOrg?.id]);

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !currentOrg) return;
    setBusy(true);
    setMessage('Uploading workspace-owned source image...');
    try {
      const uploaded = await uploadMedia(file, currentOrg.id);
      setMedia((items) => [uploaded, ...items]);
      setSourceMediaId(uploaded.id);
      setMessage('Source image uploaded.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Upload failed.');
    } finally {
      setBusy(false);
    }
  }

  function handleCompose(event: React.FormEvent) {
    event.preventDefault();
    if (!currentOrg) return;
    if (sourceMediaId === '' && !useBrandedTextCard) {
      setMessage('Choose or upload a workspace-owned image, or enable the branded quote text-card for a quote-card only.');
      return;
    }
    if (!headline.trim() || !body.trim() || !(caption || body).trim()) {
      setMessage('Write the headline, image quote/body, and accompanying caption before review.');
      return;
    }
    setComposeConfirmed(false);
    setConfirmComposeOpen(true);
  }

  async function confirmAndCompose() {
    if (!currentOrg || !composeConfirmed) return;
    setBusy(true);
    setMessage('Creating the confirmed image plus Facebook, Instagram, and LinkedIn draft packages...');
    setResults([]);
    try {
      const variants = await composeCompleteSocialPackage(currentOrg.id, {
        ...(sourceMediaId === '' ? {} : { source_media_id: sourceMediaId }),
        use_branded_text_card: useBrandedTextCard,
        template_family: templateFamily,
        background_preset: backgroundPreset,
        image_text: body,
        objective,
        creative_archetype: creativeArchetype,
        source_refs: sourceRefs.split(',').map((item) => item.trim()).filter(Boolean),
        claim_refs: claimRefs.split(',').map((item) => item.trim()).filter(Boolean),
        source_ref_ids: sourceRefIds.split(',').map((item) => Number(item.trim())).filter((item) => Number.isInteger(item) && item > 0),
        claim_ref_ids: claimRefIds.split(',').map((item) => Number(item.trim())).filter((item) => Number.isInteger(item) && item > 0),
        visual_brief: { copy_contract: 'image_text_separate_from_caption' },
        asset_provenance: { operator_selected: true },
        headline,
        body,
        caption: caption || body,
        hashtags: hashtags.split(',').map((item) => item.trim()).filter(Boolean),
        tags: tags.split(',').map((item) => item.trim()).filter(Boolean),
        cta,
        website: website || undefined,
        handle: handle || undefined,
        phone: phone || undefined,
        whatsapp: whatsapp || undefined,
        location: location || undefined,
      });
      setResults(variants);
      setMessage('Confirmed image-plus-caption packages generated as drafts/previews. Nothing was published automatically.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Template rendering failed.');
    } finally {
      setBusy(false);
      setConfirmComposeOpen(false);
    }
  }

  if (!currentOrg) return <div className="text-slate-500">Select a workspace to use Creative Studio.</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <p className="text-xs font-black tracking-widest text-indigo-600">CREATIVE STUDIO</p>
        <h1 className="text-2xl font-semibold text-slate-900 mt-1">Business-aware branded templates</h1>
        <p className="text-slate-500 mt-2">Create image-first service, product, software, technology, fashion, or quote packages for {currentOrg.name}. The studio uses your exact copy and configured business details; it does not invent prices or contact information.</p>
      </div>

      {message && <div className="rounded-lg bg-indigo-50 text-indigo-800 px-4 py-3 text-sm">{message}</div>}

      <form onSubmit={handleCompose} className="grid lg:grid-cols-[1fr_1fr] gap-6">
        <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-slate-900">1. Select visual template</h2>
            <p className="text-sm text-slate-500 mt-1">Choose the layout job before writing the copy.</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {TEMPLATE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setTemplateFamily(option.value)}
                className={`text-left rounded-lg border p-3 transition ${templateFamily === option.value ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-100' : 'border-slate-200 hover:border-indigo-300'}`}
              >
                <span className="block text-sm font-semibold text-slate-900">{option.label}</span>
                <span className="block text-xs text-slate-500 mt-1">{option.description}</span>
              </button>
            ))}
          </div>
          {templateFamily === 'quote-card' && (
            <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-4">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Choose quote background</h3>
                  <p className="text-xs text-slate-500 mt-1">Each option keeps the quote readable and reserves space for branding.</p>
                </div>
                <span className="rounded-full bg-white px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-indigo-700">{BACKGROUND_PRESETS.find((item) => item.value === backgroundPreset)?.label}</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {BACKGROUND_PRESETS.map((item) => (
                  <button key={item.value} type="button" onClick={() => setBackgroundPreset(item.value)} className={`overflow-hidden rounded-lg border text-left bg-white transition ${backgroundPreset === item.value ? 'border-indigo-600 ring-2 ring-indigo-200' : 'border-slate-200 hover:border-indigo-300'}`}>
                    <span className="block h-12" style={{ background: item.swatch }} />
                    <span className="block px-2 py-1.5"><span className="block text-xs font-semibold text-slate-900">{item.label}</span><span className="block text-[10px] leading-tight text-slate-500 mt-0.5">{item.description}</span></span>
                  </button>
                ))}
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Source image or branded text-card</label>
            <select value={sourceMediaId} onChange={(event) => setSourceMediaId(event.target.value ? Number(event.target.value) : '')} className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white text-sm">
              <option value="">No source — use branded text-card</option>
              {media.map((item) => <option key={item.id} value={item.id}>{item.filename}</option>)}
            </select>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={useBrandedTextCard} onChange={(event) => { setUseBrandedTextCard(event.target.checked); if (event.target.checked) setTemplateFamily('quote-card'); }} />
              Use branded quote text-card background
            </label>
            <label className="inline-block mt-2 text-sm text-indigo-700 cursor-pointer hover:underline">
              Upload new product/background image
              <input type="file" accept="image/*" onChange={handleUpload} className="hidden" />
            </label>
          </div>
        </section>

        <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-slate-900">2. Define the marketing job</h2>
            <p className="text-sm text-slate-500 mt-1">Choose the objective and archetype before writing. Evidence references are optional but should point to approved workspace sources or claims.</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="text-sm text-slate-700">Objective<select value={objective} onChange={(event) => setObjective(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 bg-white text-sm">{OBJECTIVE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
            <label className="text-sm text-slate-700">Creative archetype<input value={creativeArchetype} onChange={(event) => setCreativeArchetype(event.target.value)} placeholder="service-announcement" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
            <input value={sourceRefs} onChange={(event) => setSourceRefs(event.target.value)} placeholder="Source notes, comma separated" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2" />
            <input value={claimRefs} onChange={(event) => setClaimRefs(event.target.value)} placeholder="Claim notes, comma separated" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2" />
            <input value={sourceRefIds} onChange={(event) => setSourceRefIds(event.target.value)} placeholder="Approved source IDs, e.g. 12, 13" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <input value={claimRefIds} onChange={(event) => setClaimRefIds(event.target.value)} placeholder="Approved claim IDs, e.g. 4, 5" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900">3. Write the exact creative copy</h2>
            <p className="text-sm text-slate-500 mt-1">The headline/body/CTA are printed on the image. The caption, hashtags, and tags are the text that accompanies the image when posted.</p>
          </div>
          <input value={headline} onChange={(event) => setHeadline(event.target.value)} placeholder="Headline / collection / quote title" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Text printed on the image: quote, product detail, styling line, or collection story" rows={4} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <textarea value={caption} onChange={(event) => setCaption(event.target.value)} placeholder="Post caption that appears with the image" rows={5} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <input value={hashtags} onChange={(event) => setHashtags(event.target.value)} placeholder={isQuoteWorkspace ? 'Hashtags, comma separated: hinglishquotes, dilkibaat' : 'Hashtags, comma separated: fashion, tailoring, style'} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Tags or mentions, comma separated: @brand, quote community" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <input value={cta} onChange={(event) => setCta(event.target.value)} placeholder={isQuoteWorkspace ? 'CTA: Agar dil ko laga, share karo.' : 'CTA: Book a consultation / WhatsApp us / Visit the studio'} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <div className="grid sm:grid-cols-2 gap-3">
            <input value={handle} onChange={(event) => setHandle(event.target.value)} placeholder="Instagram/Facebook handle" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <input value={website} onChange={(event) => setWebsite(event.target.value)} placeholder="Website" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <input value={whatsapp} onChange={(event) => setWhatsapp(event.target.value)} placeholder="WhatsApp display number" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Public phone" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Studio/location" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2" />
          </div>
          <button type="submit" disabled={busy} className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50">Review & confirm compose</button>
          <p className="text-xs text-slate-500">The image text stays separate from the longer caption. No image, package, or draft is created until you confirm the reviewed creative brief.</p>
          {confirmComposeOpen && (
            <div className="rounded-xl border-2 border-amber-300 bg-amber-50 p-4" role="dialog" aria-modal="true" aria-labelledby="studio-confirm-title">
              <p className="text-[10px] font-black uppercase tracking-widest text-amber-700">Final creative check</p>
              <h3 id="studio-confirm-title" className="mt-1 text-base font-semibold text-amber-950">Confirm image package creation</h3>
              <p className="mt-2 text-sm leading-relaxed text-amber-900">Create Facebook, Instagram, and LinkedIn draft previews for <strong>{currentOrg.name}</strong> using <strong>{BACKGROUND_PRESETS.find((item) => item.value === backgroundPreset)?.label}</strong>. This does not publish, schedule, send, boost, or submit for approval.</p>
              <label className="mt-3 flex items-start gap-2 text-sm text-amber-950"><input type="checkbox" checked={composeConfirmed} onChange={(event) => setComposeConfirmed(event.target.checked)} className="mt-1" /><span>I reviewed the quote, background template, caption, CTA, hashtags, and tags. Create the draft package.</span></label>
              <div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={confirmAndCompose} disabled={!composeConfirmed || busy} className="rounded-lg bg-amber-700 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-800 disabled:opacity-50">{busy ? 'Creating...' : 'Confirm & create package'}</button><button type="button" onClick={() => setConfirmComposeOpen(false)} className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-semibold text-amber-900 hover:bg-amber-100">Cancel — create nothing</button></div>
            </div>
          )}
        </section>
      </form>

      <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">3. Review before approval</h2>
        <p className="text-sm text-slate-500 mt-1">Each card below contains the image and the exact social copy package for that platform. Publishing still requires the existing human approval gate.</p>
        {results.length === 0 ? <p className="text-sm text-slate-500 mt-4">No complete post package generated yet.</p> : (
          <div className="grid md:grid-cols-3 gap-4 mt-4">
            {results.map((post) => (
              <div key={post.package_id} className="rounded-lg border border-slate-200 overflow-hidden bg-slate-50">
                <img src={post.image.url} alt={post.alt_text || `${post.platform} creative: ${post.headline}`} className="block h-auto w-full object-contain bg-slate-100" />
                <div className="p-3 space-y-2">
                  <div className="flex items-center justify-between"><span className="text-xs font-black uppercase tracking-wider text-indigo-700">{post.platform}</span><span className="text-[11px] text-slate-500">{post.status}</span></div>
                  <p className="text-sm font-semibold text-slate-900">{post.headline}</p>
                  <p className="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-900"><strong>Image text:</strong> {post.image_text || 'Not recorded'}</p>
                  <p className="text-xs text-slate-700 whitespace-pre-wrap">{post.caption}</p>
                  {post.cta && <p className="text-xs font-semibold text-indigo-700">CTA: {post.cta}</p>}
                  <p className="text-xs text-slate-500 break-words">{post.hashtags.join(' ')}</p>
                  {post.tags.length > 0 && <p className="text-xs text-slate-500 break-words">Tags: {post.tags.join(', ')}</p>}
                  <p className="text-[11px] text-slate-500">{post.objective || 'awareness'} · {post.creative_archetype || 'not specified'} · Evidence: {post.evidence_status || 'unverified'} · QA: {post.visual_qa_status || 'not_run'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
