import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import { listMedia, uploadMedia, type Media } from '../api/media';
import { composeCompleteSocialPackage, type CompleteSocialPostPackage, type CompleteSocialPostComposeRequest } from '../api/remainingRoadmap';

const TEMPLATE_OPTIONS = [
  { value: 'fashion-editorial', label: 'Fashion editorial', description: 'Premium image-led card with an elegant text-safe panel.' },
  { value: 'product-catalog', label: 'Product catalog', description: 'Product-first card with design details and inquiry CTA.' },
  { value: 'quote-card', label: 'Quote card', description: 'Large quote, quotation mark, highlighted identity, and footer.' },
  { value: 'collection-story', label: 'Collection story', description: 'Stacked collection title, inspiration, quote, and CTA zones.' },
] as const;

export default function CreativeStudio() {
  const { currentOrg } = useOrg();
  const [media, setMedia] = useState<Media[]>([]);
  const [sourceMediaId, setSourceMediaId] = useState<number | ''>('');
  const [useBrandedTextCard, setUseBrandedTextCard] = useState(false);
  const [templateFamily, setTemplateFamily] = useState<CompleteSocialPostComposeRequest['template_family']>('fashion-editorial');
  const [headline, setHeadline] = useState('');
  const [body, setBody] = useState('');
  const [caption, setCaption] = useState('');
  const [hashtags, setHashtags] = useState('fashion, style, tailoring');
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
      setUseBrandedTextCard(true);
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

  async function handleCompose(event: React.FormEvent) {
    event.preventDefault();
    if (!currentOrg) return;
    if (sourceMediaId === '' && !useBrandedTextCard) {
      setMessage('Choose or upload a workspace-owned image, or enable the branded quote text-card.');
      return;
    }
    setBusy(true);
    setMessage('Creating the image plus Facebook, Instagram, and LinkedIn post packages...');
    setResults([]);
    try {
      const variants = await composeCompleteSocialPackage(currentOrg.id, {
        ...(sourceMediaId === '' ? {} : { source_media_id: sourceMediaId }),
        use_branded_text_card: useBrandedTextCard,
        template_family: templateFamily,
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
      setMessage('Complete image-plus-caption packages generated. They are drafts/previews and are not published automatically.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Template rendering failed.');
    } finally {
      setBusy(false);
    }
  }

  if (!currentOrg) return <div className="text-slate-500">Select a workspace to use Creative Studio.</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <p className="text-xs font-black tracking-widest text-indigo-600">CREATIVE STUDIO</p>
        <h1 className="text-2xl font-semibold text-slate-900 mt-1">Business-aware branded templates</h1>
        <p className="text-slate-500 mt-2">Create quote cards, suit showcases, collection stories, and consultation creatives for {currentOrg.name}. The studio uses your exact copy and configured business details; it does not invent prices or contact information.</p>
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
            <h2 className="font-semibold text-slate-900">2. Write the exact creative copy</h2>
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
          <button type="submit" disabled={busy} className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50">{busy ? 'Rendering...' : 'Generate branded variants'}</button>
        </section>
      </form>

      <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">3. Review before approval</h2>
        <p className="text-sm text-slate-500 mt-1">Each card below contains the image and the exact social copy package for that platform. Publishing still requires the existing human approval gate.</p>
        {results.length === 0 ? <p className="text-sm text-slate-500 mt-4">No complete post package generated yet.</p> : (
          <div className="grid md:grid-cols-3 gap-4 mt-4">
            {results.map((post) => (
              <div key={post.package_id} className="rounded-lg border border-slate-200 overflow-hidden bg-slate-50">
                <img src={post.image.url} alt={`${post.platform} creative: ${post.headline}`} className="w-full aspect-square object-cover bg-slate-100" />
                <div className="p-3 space-y-2">
                  <div className="flex items-center justify-between"><span className="text-xs font-black uppercase tracking-wider text-indigo-700">{post.platform}</span><span className="text-[11px] text-slate-500">{post.status}</span></div>
                  <p className="text-sm font-semibold text-slate-900">{post.headline}</p>
                  <p className="text-xs text-slate-700 whitespace-pre-wrap">{post.caption}</p>
                  {post.cta && <p className="text-xs font-semibold text-indigo-700">CTA: {post.cta}</p>}
                  <p className="text-xs text-slate-500 break-words">{post.hashtags.join(' ')}</p>
                  {post.tags.length > 0 && <p className="text-xs text-slate-500 break-words">Tags: {post.tags.join(', ')}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
