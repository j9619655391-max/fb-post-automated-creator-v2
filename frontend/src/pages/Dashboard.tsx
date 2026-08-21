import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listContent, type Content } from '../api/content';
import { listScheduledPosts, cancelScheduledPost, retryScheduledPost, type ScheduledPost } from '../api/scheduledPosts';
import { getAIProviderHealth, getAIProviderStatus, type AIProviderHealth, type AIProviderStatus } from '../api/generation';

function scheduleStatusLabel(status: string): string {
  switch (status) {
    case 'pending': return 'Scheduled';
    case 'processing': return 'Processing';
    case 'retrying': return 'Retrying';
    case 'posted': return 'Posted';
    case 'partially_failed': return 'Partially failed';
    case 'failed': return 'Failed';
    case 'dead_letter': return 'Needs review';
    case 'cancelled': return 'Cancelled';
    default: return status;
  }
}

function scheduleStatusClass(status: string): string {
  switch (status) {
    case 'pending': return 'bg-blue-100 text-blue-800';
    case 'processing': return 'bg-amber-100 text-amber-800';
    case 'retrying': return 'bg-amber-100 text-amber-800';
    case 'posted': return 'bg-emerald-100 text-emerald-800';
    case 'partially_failed': return 'bg-orange-100 text-orange-800';
    case 'failed': return 'bg-red-100 text-red-800';
    case 'dead_letter': return 'bg-red-100 text-red-800';
    case 'cancelled': return 'bg-slate-100 text-slate-600';
    default: return 'bg-slate-100 text-slate-600';
  }
}

export default function Dashboard() {
  const { isAuthenticated } = useAuth();
  const [content, setContent] = useState<Content[]>([]);
  const [scheduled, setScheduled] = useState<ScheduledPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null);
  const [providerHealth, setProviderHealth] = useState<AIProviderHealth | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    listContent({ limit: 50 })
      .then(setContent)
      .catch(() => setContent([]));
        listScheduledPosts({ limit: 20 })
      .then(setScheduled)
      .catch(() => setScheduled([]))
      .finally(() => setLoading(false));
    getAIProviderStatus()
      .then(setProviderStatus)
      .catch(() => setProviderStatus(null));
    getAIProviderHealth()
      .then(setProviderHealth)
      .catch(() => setProviderHealth(null));

  }, [isAuthenticated]);

  const byStatus = content.reduce<Record<string, number>>((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {});
  const pending = byStatus['pending_approval'] ?? 0;
  const approved = byStatus['approved'] ?? 0;
  const draft = byStatus['draft'] ?? 0;

  async function refreshScheduled() {
    setScheduled(await listScheduledPosts({ limit: 20 }));
  }

  async function handleRetry(postId: number) {
    if (!isAuthenticated) return;
    try {
      await retryScheduledPost(postId);
      await refreshScheduled();
    } catch (err) {
      alert('Failed to retry scheduled post');
    }
  }

  function handleReauthenticate() {
    window.location.assign('/platforms');
  }

  async function handleCancel(postId: number) {
    if (!isAuthenticated || !window.confirm('Cancel this scheduled post?')) return;
    try {
      await cancelScheduledPost(postId);
      await refreshScheduled();
    } catch (err) {
      alert('Failed to cancel post');
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Dashboard</h1>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-slate-500 text-sm font-medium">Drafts</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{draft}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-slate-500 text-sm font-medium">Pending approval</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{pending}</p>
        </div>
                <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-slate-500 text-sm font-medium">Approved</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{approved}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-slate-500 text-sm font-medium">AI provider</p>
          <p className="text-lg font-bold text-indigo-700 mt-1">
            {providerStatus?.provider ?? 'Checking...'}
          </p>
          <p className="text-xs text-slate-500 mt-1 truncate" title={providerStatus?.model ?? undefined}>
            {providerStatus?.model ?? 'Provider status unavailable'}
          </p>
          {providerStatus && (
            <p className={`text-xs mt-2 ${providerStatus.configured ? 'text-emerald-600' : 'text-red-600'}`}>
              {providerStatus.configured ? (providerStatus.free_model ? 'Free model configured' : 'Configured') : 'Not configured'}
            </p>
          )}
          {providerHealth?.alert && (
            <p className="text-xs mt-1 text-red-600" title={providerHealth.alert_reason ?? undefined}>
              Alert: {providerHealth.failed_jobs} failures · {providerHealth.retrying_plans} retries
            </p>
          )}
        </div>

      </div>

      {scheduled.length > 0 && (
        <>
          <h2 className="text-lg font-medium text-slate-800 mb-3">Scheduled posts</h2>
          <ul className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100 overflow-hidden mb-8">
            {scheduled.map((sp) => (
              <li key={sp.id} className="relative block px-4 py-3 hover:bg-slate-50 flex items-center justify-between gap-2 min-h-[72px]">
                <Link to={`/content/${sp.content_id}`} className="flex-1 flex items-center justify-between gap-2">
                  <span className="text-slate-900">Content #{sp.content_id} · {sp.provider_label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-sm shrink-0">
                      {new Date(sp.scheduled_at).toLocaleString()}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${scheduleStatusClass(sp.status)}`}>
                      {scheduleStatusLabel(sp.status)}
                    </span>
                  </div>
                </Link>
                {(sp.failure_reason || sp.recovery_hint) && (
                  <div className="absolute left-4 right-4 mt-16 text-xs text-slate-500">
                    {sp.last_error_code && <span className="font-semibold text-slate-600">{sp.last_error_code}: </span>}
                    {sp.recovery_hint || sp.failure_reason}
                  </div>
                )}
                <div className="flex items-center gap-2 ml-2 shrink-0">
                  {(sp.recovery_action === 'reauthenticate') && (
                    <button
                      onClick={handleReauthenticate}
                      className="text-xs border border-amber-300 rounded px-2 py-1 text-amber-700 hover:bg-amber-50"
                    >
                      Re-authenticate
                    </button>
                  )}
                  {(sp.recovery_action === 'retry' || sp.recovery_action === 'reauthenticate' || sp.retryable) && (
                    <button
                      onClick={() => handleRetry(sp.id)}
                      className="text-xs border border-indigo-300 rounded px-2 py-1 text-indigo-700 hover:bg-indigo-50"
                    >
                      Retry job
                    </button>
                  )}
                  {(sp.status === 'pending' || sp.status === 'retrying') && (
                    <button
                      onClick={() => handleCancel(sp.id)}
                      className="text-xs border border-slate-300 rounded px-2 py-1 text-slate-600 hover:bg-slate-100"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-slate-800">Recent content</h2>
        <Link to="/content/new" className="text-indigo-600 hover:underline font-medium text-sm">New content</Link>
      </div>
      {loading ? (
        <p className="text-slate-500">Loading...</p>
      ) : content.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
          No content yet. <Link to="/content/new" className="text-indigo-600 hover:underline">Create one</Link>.
        </div>
      ) : (
        <ul className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100 overflow-hidden">
          {content.slice(0, 10).map((c) => (
            <li key={c.id}>
              <Link to={`/content/${c.id}`} className="block px-4 py-3 hover:bg-slate-50 flex items-center justify-between">
                <span className="font-medium text-slate-900">{c.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${c.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                  c.status === 'pending_approval' ? 'bg-amber-100 text-amber-800' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                  {c.status}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
