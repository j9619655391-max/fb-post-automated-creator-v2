import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listContent, type Content } from '../api/content';
import { listScheduledPosts, type ScheduledPost } from '../api/scheduledPosts';
import { useOrg } from '../context/OrgContext';

interface CalendarItem {
  content: Content;
  job: ScheduledPost;
}

function statusLabel(status: ScheduledPost['status']) {
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

export default function Calendar() {
  const { currentOrg } = useOrg();
  const [scheduledItems, setScheduledItems] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      listContent({ status: 'approved', organization_id: currentOrg?.id }),
      listScheduledPosts({ limit: 100 }),
    ])
      .then(([content, jobs]) => {
        const contentById = new Map(content.map((item) => [item.id, item]));
        const items = jobs
          .map((job) => ({ content: contentById.get(job.content_id), job }))
          .filter((item): item is CalendarItem => Boolean(item.content))
          .filter(({ job }) => job.status !== 'cancelled')
          .sort((a, b) => new Date(a.job.scheduled_at).getTime() - new Date(b.job.scheduled_at).getTime());
        setScheduledItems(items);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load schedule'))
      .finally(() => setLoading(false));
  }, [currentOrg]);

  if (loading) return <p className="text-slate-500">Loading your content calendar...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Content Calendar</h1>
        <p className="text-slate-600">Monitor approved posts that are actually queued for automatic publishing.</p>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {scheduledItems.length === 0 ? (
        <div className="p-16 rounded-2xl border-2 border-dashed border-slate-200 text-center bg-slate-50">
          <h3 className="text-xl font-bold text-slate-900 mb-2">Queue is empty</h3>
          <p className="text-slate-500 max-w-md mx-auto mb-6 text-sm">Create or generate a draft, approve it, and schedule it for automatic publishing.</p>
          <Link to="/content/new" className="inline-flex rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-600">Start drafting</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {scheduledItems.map(({ content, job }) => (
            <div key={job.id} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col lg:flex-row lg:items-center gap-5">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">{new Date(job.scheduled_at).toLocaleString()}</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-slate-100 text-slate-700">{statusLabel(job.status)}</span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 truncate">{content.title}</h3>
                <p className="text-sm text-slate-600 line-clamp-2 mt-1">{content.body}</p>
                {job.failure_reason && <p className="text-sm text-red-600 mt-2">{job.failure_reason}</p>}
              </div>
              <Link to={`/content/${content.id}`} className="px-4 py-2 rounded-lg bg-slate-50 text-sm font-semibold text-slate-900 hover:bg-slate-900 hover:text-white border border-slate-100">Review content</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
