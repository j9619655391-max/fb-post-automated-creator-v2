import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getContent, listContentPackages, submitForApproval, approveContent, deleteContent, publishToFacebook, publishToLinkedIn, type Content } from '../api/content';
import type { ContentPackage } from '../api/contentPackages';
import { listPages, type MetaPage } from '../api/metaPages';
import { listLinkedInAccounts, type LinkedInAccount } from '../api/platforms';

export default function ContentDetail() {
  const { isAuthenticated } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState<Content | null>(null);
  const [packages, setPackages] = useState<ContentPackage[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [approveComment, setApproveComment] = useState('');
  const [pages, setPages] = useState<MetaPage[]>([]);
  const [selectedPageIds, setSelectedPageIds] = useState<number[]>([]);
  const [linkedinAccounts, setLinkedinAccounts] = useState<LinkedInAccount[]>([]);
  const [selectedLinkedInIds, setSelectedLinkedInIds] = useState<number[]>([]);
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishLinkedInLoading, setPublishLinkedInLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !id) return;
    getContent(parseInt(id, 10)).then(setContent).catch(() => setError('Content not found'));
  }, [isAuthenticated, id]);

  useEffect(() => {
    if (!isAuthenticated) return;
    listPages().then(setPages).catch(() => setPages([]));
    listLinkedInAccounts().then(setLinkedinAccounts).catch(() => setLinkedinAccounts([]));
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated || !id || !content?.organization_id) {
      setPackages([]);
      return;
    }
    listContentPackages(parseInt(id, 10), content.organization_id)
      .then(setPackages)
      .catch(() => setPackages([]));
  }, [isAuthenticated, id, content?.organization_id]);

  async function handleSubmit() {
    if (!isAuthenticated || !id || !content) return;
    setLoading(true);
    setError('');
    try {
      const updated = await submitForApproval(parseInt(id, 10));
      setContent(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit');
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(approved: boolean) {
    if (!isAuthenticated || !id || !content) return;
    setLoading(true);
    setError('');
    try {
      const updated = await approveContent(parseInt(id, 10), { approved, comment: approveComment || undefined });
      setContent(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!isAuthenticated || !id || !content) return;
    if (!window.confirm('Delete this content?')) return;
    setLoading(true);
    setError('');
    try {
      await deleteContent(parseInt(id, 10));
      navigate('/content', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setLoading(false);
    }
  }

  async function handlePublishToFacebook() {
    if (!isAuthenticated || !id || !content || selectedPageIds.length === 0) return;
    setPublishLoading(true);
    setError('');
    try {
      const updated = await publishToFacebook(parseInt(id, 10), selectedPageIds);
      setContent(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish to Facebook');
    } finally {
      setPublishLoading(false);
    }
  }

  async function handlePublishToLinkedIn() {
    if (!isAuthenticated || !id || !content || selectedLinkedInIds.length === 0) return;
    setPublishLinkedInLoading(true);
    setError('');
    try {
      const updated = await publishToLinkedIn(parseInt(id, 10), selectedLinkedInIds);
      setContent(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish to LinkedIn');
    } finally {
      setPublishLinkedInLoading(false);
    }
  }

  if (error && !content) {
    return (
      <div>
        <p className="text-red-600">{error}</p>
        <Link to="/content" className="text-indigo-600 hover:underline mt-2 inline-block">Back to list</Link>
      </div>
    );
  }
  if (!content) return <p className="text-slate-500">Loading...</p>;

  const canEdit = content.status === 'draft';
  const canSubmit = content.status === 'draft';
  const canApprove = content.status === 'pending_approval';
  const statusClass =
    content.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
      content.status === 'pending_approval' ? 'bg-amber-100 text-amber-800' :
        content.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-600';

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-slate-900">{content.title}</h1>
        <span className={'text-sm px-2 py-1 rounded-full ' + statusClass}>{content.status}</span>
      </div>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
        <p className="text-slate-700 whitespace-pre-wrap mb-4">{content.body}</p>
        {content.media && (
          <div className="mb-4 rounded-lg overflow-hidden border border-slate-200 max-w-xl bg-slate-50">
            {content.media.mime_type.startsWith('video/') ? (
              <video src={content.media.url} controls className="w-full h-auto" />
            ) : (
              <img src={content.media.url} alt="Attached media" className="w-full h-auto" />
            )}
          </div>
        )}
        <p className="text-slate-400 text-sm">
          Created {new Date(content.created_at).toLocaleString()}
          {content.approved_at && ' · Approved ' + new Date(content.approved_at).toLocaleString()}
          {content.publish_statuses?.length > 0 && ` · Published to ${content.publish_statuses.filter(s => s.status === 'posted').length} targets`}
        </p>
      </div>
      {packages.length > 0 && (
        <section className="mb-6 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
          <div className="flex items-start justify-between gap-4"><div><h2 className="text-lg font-bold text-indigo-950">Complete social post package</h2><p className="mt-1 text-sm text-indigo-800">The image and the text that accompanies it are stored together for review. Publishing is still blocked until approval.</p></div><span className="rounded-full bg-white px-3 py-1 text-xs font-bold uppercase tracking-wide text-indigo-700">{packages.length} platforms</span></div>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {packages.map((post) => (
              <article key={post.id} className="overflow-hidden rounded-xl border border-indigo-100 bg-white">
                {post.media_variant_urls?.[0] ? <img src={post.media_variant_urls[0]} alt={post.alt_text || `${post.platform} generated creative`} className="block h-auto w-full object-contain bg-slate-100" /> : <div className="flex min-h-48 items-center justify-center bg-slate-100"><p className="px-4 text-center text-xs text-slate-500">Image preview is not available for this package.</p></div>}
                <div className="space-y-2 p-4">
                  <div className="flex items-center justify-between"><span className="text-xs font-black uppercase tracking-widest text-indigo-700">{post.platform}</span><span className="text-[11px] font-semibold text-slate-500">{post.status}</span></div>
                  <p className="text-sm font-semibold text-slate-900">{post.headline}</p>
                  <p className="rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-900"><strong>Image text:</strong> {post.image_text || 'Not recorded'}</p>
                  <p className="whitespace-pre-wrap text-xs text-slate-700">{post.caption}</p>
                  {post.cta && <p className="text-xs font-bold text-indigo-700">CTA: {post.cta}</p>}
                  <p className="break-words text-xs text-slate-500">{post.hashtags.join(' ')}</p>
                  {post.tags.length > 0 && <p className="break-words text-xs text-slate-500">Tags: {post.tags.join(', ')}</p>}
                  <div className="border-t border-indigo-100 pt-2 text-[11px] text-slate-500">
                    <p><strong>Objective:</strong> {post.objective || 'Not specified'} · <strong>Archetype:</strong> {post.creative_archetype || 'Not specified'}</p>
                    <p><strong>Asset:</strong> {String(post.asset_provenance?.mode || 'Not specified')} · <strong>Evidence:</strong> {post.evidence_status || 'unverified'} · <strong>Visual QA:</strong> {post.visual_qa_status || 'not_run'}</p>
                    {((post.source_ref_ids || []).length > 0 || (post.claim_ref_ids || []).length > 0) && <p><strong>Evidence IDs:</strong> sources {(post.source_ref_ids || []).join(', ') || 'none'} · claims {(post.claim_ref_ids || []).join(', ') || 'none'}</p>}
                    {(post.source_refs || []).length > 0 && <p className="break-words"><strong>Evidence:</strong> {(post.source_refs || []).join(' · ')}</p>}
                    {(post.claim_refs || []).length > 0 && <p className="break-words"><strong>Claims:</strong> {(post.claim_refs || []).join(' · ')}</p>}
                    {(post.visual_qa_flags || []).length > 0 && <p className="break-words text-amber-700"><strong>QA flags:</strong> {(post.visual_qa_flags || []).join(', ')}</p>}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <div className="flex flex-wrap gap-2">
        {canEdit && (
          <Link to={'/content/' + id + '/edit'} className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50">
            Edit
          </Link>
        )}
        {canSubmit && (
          <button type="button" onClick={handleSubmit} disabled={loading} className="rounded-lg bg-amber-600 text-white px-4 py-2 hover:bg-amber-700 disabled:opacity-50">
            Submit for approval
          </button>
        )}
        {canEdit && (
          <button type="button" onClick={handleDelete} disabled={loading} className="rounded-lg border border-red-300 text-red-700 px-4 py-2 hover:bg-red-50 disabled:opacity-50">
            Delete
          </button>
        )}
        {canApprove && (
          <>
            <input type="text" placeholder="Comment (optional)" value={approveComment} onChange={(e) => setApproveComment(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <button type="button" onClick={() => handleApprove(true)} disabled={loading} className="rounded-lg bg-emerald-600 text-white px-4 py-2 hover:bg-emerald-700 disabled:opacity-50">Approve</button>
            <button type="button" onClick={() => handleApprove(false)} disabled={loading} className="rounded-lg bg-red-600 text-white px-4 py-2 hover:bg-red-700 disabled:opacity-50">Reject</button>
          </>
        )}
      </div>
      <div className="grid md:grid-cols-2 gap-6 mt-6">
        {/* Facebook Section */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <h2 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <span className="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-[10px]">FB</span>
            Publish to Facebook
          </h2>
          {content.status !== 'approved' ? (
            <p className="text-slate-500 text-sm">Content must be <strong>Approved</strong> first.</p>
          ) : (
            <>
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-2 max-h-32 overflow-y-auto w-full p-2 border border-slate-200 rounded-lg bg-white">
                  {pages.map((p) => (
                    <label key={p.id} className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedPageIds.includes(p.id)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedPageIds([...selectedPageIds, p.id]);
                          else setSelectedPageIds(selectedPageIds.filter(idStr => idStr !== p.id));
                        }}
                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                      />
                      {p.page_name || p.page_id}
                    </label>
                  ))}
                  {pages.length === 0 && <p className="text-slate-400 text-xs italic">No pages found.</p>}
                </div>
                <button
                  type="button"
                  onClick={handlePublishToFacebook}
                  disabled={publishLoading || selectedPageIds.length === 0 || pages.length === 0}
                  className="w-full rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {publishLoading ? 'Publishing...' : 'Publish to Facebook'}
                </button>
              </div>
            </>
          )}
        </div>

        {/* LinkedIn Section */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <h2 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <span className="w-5 h-5 bg-blue-800 text-white rounded-full flex items-center justify-center text-[10px]">IN</span>
            Publish to LinkedIn
          </h2>
          {content.status !== 'approved' ? (
            <p className="text-slate-500 text-sm">Content must be <strong>Approved</strong> first.</p>
          ) : (
            <>
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-2 max-h-32 overflow-y-auto w-full p-2 border border-slate-200 rounded-lg bg-white">
                  {linkedinAccounts.map((acc) => (
                    <label key={acc.id} className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedLinkedInIds.includes(acc.id)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedLinkedInIds([...selectedLinkedInIds, acc.id]);
                          else setSelectedLinkedInIds(selectedLinkedInIds.filter(id => id !== acc.id));
                        }}
                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                      />
                      {acc.name}
                    </label>
                  ))}
                  {linkedinAccounts.length === 0 && <p className="text-slate-400 text-xs italic">No LinkedIn accounts found.</p>}
                </div>
                <button
                  type="button"
                  onClick={handlePublishToLinkedIn}
                  disabled={publishLinkedInLoading || selectedLinkedInIds.length === 0 || linkedinAccounts.length === 0}
                  className="w-full rounded-lg bg-blue-800 text-white px-4 py-2 text-sm font-medium hover:bg-blue-900 disabled:opacity-50"
                >
                  {publishLinkedInLoading ? 'Publishing...' : 'Publish to LinkedIn'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
