import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import { listMedia, uploadMedia, type Media } from '../api/media';
import { composeBrandedMedia, type BrandedMediaVariant, type BrandedMediaComposeRequest } from '../api/remainingRoadmap';

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
  const [templateFamily, setTemplateFamily] = useState<BrandedMediaComposeRequest['template_family']>('fashion-editorial');
  const [headline, setHeadline] = useState('');
  const [body, setBody] = useState('');
  const [cta, setCta] = useState('Message us for a consultation');
  const [website, setWebsite] = useState('');
  const [handle, setHandle] = useState('');
  const [phone, setPhone] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [location, setLocation] = useState('');
  const [results, setResults] = useState<BrandedMediaVariant[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

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
    if (!currentOrg || sourceMediaId === '') {
      setMessage('Choose or upload a workspace-owned image first.');
      return;
    }
    setBusy(true);
    setMessage('Rendering three platform-specific branded variants...');
    setResults([]);
    try {
      const variants = await composeBrandedMedia(currentOrg.id, {
        source_media_id: sourceMediaId,
        template_family: templateFamily,
        headline,
        body,
        cta,
        website: website || undefined,
        handle: handle || undefined,
        phone: phone || undefined,
        whatsapp: whatsapp || undefined,
        location: location || undefined,
      });
      setResults(variants);
      setMessage('Variants generated. They are stored as drafts/assets and are not published automatically.');
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
            <label className="block text-sm font-medium text-slate-700 mb-1">Source image</label>
            <select value={sourceMediaId} onChange={(event) => setSourceMediaId(event.target.value ? Number(event.target.value) : '')} className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white text-sm">
              <option value="">Choose uploaded image...</option>
              {media.map((item) => <option key={item.id} value={item.id}>{item.filename}</option>)}
            </select>
            <label className="inline-block mt-2 text-sm text-indigo-700 cursor-pointer hover:underline">
              Upload new product/background image
              <input type="file" accept="image/*" onChange={handleUpload} className="hidden" />
            </label>
          </div>
        </section>

        <section className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-slate-900">2. Write the exact creative copy</h2>
            <p className="text-sm text-slate-500 mt-1">For a fashion business, use product, collection, fabric, styling, occasion, booking, or fashion-quote intent.</p>
          </div>
          <input value={headline} onChange={(event) => setHeadline(event.target.value)} placeholder="Headline / collection / quote title" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Quote, product description, fabric detail, styling tip, or collection story" rows={5} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <input value={cta} onChange={(event) => setCta(event.target.value)} placeholder="CTA: Book a consultation / WhatsApp us / Visit the studio" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
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
        <p className="text-sm text-slate-500 mt-1">Generated assets are previews only. Publishing still requires the existing human approval gate.</p>
        {results.length === 0 ? <p className="text-sm text-slate-500 mt-4">No variants generated yet.</p> : (
          <div className="grid md:grid-cols-3 gap-4 mt-4">
            {results.map((variant) => (
              <div key={variant.id} className="rounded-lg border border-slate-200 overflow-hidden">
                <img src={variant.url} alt={variant.filename} className="w-full aspect-square object-cover bg-slate-100" />
                <p className="px-3 py-2 text-xs text-slate-600 truncate" title={variant.filename}>{variant.filename}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
