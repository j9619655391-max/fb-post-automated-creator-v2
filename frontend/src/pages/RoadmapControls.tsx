import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import {
  clearEmergencyStop,
  collectSignals,
  getAnalyticsSummary,
  getAutomationPolicy,
  getSignalSummary,
  triggerEmergencyStop,
  updateAutomationPolicy,
  type AnalyticsSummary,
  type AutomationPolicy,
  type SignalSummary,
} from '../api/remainingRoadmap';

export default function RoadmapControls() {
  const { currentOrg } = useOrg();
  const [signals, setSignals] = useState<SignalSummary | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [policy, setPolicy] = useState<AutomationPolicy | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  async function refresh() {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [signalSummary, performance, automation] = await Promise.all([
        getSignalSummary(currentOrg.id),
        getAnalyticsSummary(currentOrg.id),
        getAutomationPolicy(currentOrg.id),
      ]);
      setSignals(signalSummary);
      setAnalytics(performance);
      setPolicy(automation);
    } catch {
      setMessage('Unable to load workspace intelligence controls.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, [currentOrg?.id]);

  async function handleCollect() {
    if (!currentOrg) return;
    setMessage('Collecting trusted source signals...');
    try {
      await collectSignals(currentOrg.id);
      await refresh();
      setMessage('Signal collection completed.');
    } catch {
      setMessage('Signal collection failed; verify configured sources.');
    }
  }

  async function handleEmergencyStop() {
    if (!currentOrg || !window.confirm('Stop controlled automation for this workspace?')) return;
    try {
      setPolicy(await triggerEmergencyStop(currentOrg.id, 'Stopped by workspace operator'));
      setMessage('Emergency stop is active. No controlled autopilot may proceed.');
    } catch {
      setMessage('Unable to activate the emergency stop.');
    }
  }

  async function handleClearStop() {
    if (!currentOrg) return;
    try {
      setPolicy(await clearEmergencyStop(currentOrg.id));
      setMessage('Emergency stop cleared; approval-required mode remains unchanged.');
    } catch {
      setMessage('Unable to clear the emergency stop.');
    }
  }

  async function toggleControlledMode() {
    if (!currentOrg || !policy) return;
    try {
      const next = policy.approval_mode === 'controlled' ? 'required' : 'controlled';
      setPolicy(await updateAutomationPolicy(currentOrg.id, {
        approval_mode: next,
        autopilot_enabled: next === 'controlled' && policy.autopilot_enabled,
        max_autopilot_risk_tier: policy.max_autopilot_risk_tier,
        max_autopilot_posts_per_day: policy.max_autopilot_posts_per_day,
        max_approval_batch_size: policy.max_approval_batch_size,
        approval_batch_window_minutes: policy.approval_batch_window_minutes,
        max_daily_generated_drafts: policy.max_daily_generated_drafts,
        emergency_stop: policy.emergency_stop,
        emergency_stop_reason: policy.emergency_stop_reason,
      }));
      setMessage(next === 'controlled' ? 'Controlled mode enabled; existing risk and daily caps still apply.' : 'Approval-required mode restored.');
    } catch {
      setMessage('Unable to update the workspace automation policy.');
    }
  }

  if (!currentOrg) return <div className="text-slate-500">Select a workspace to view controls.</div>;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-black tracking-widest text-indigo-600">OPERATING SYSTEM</p>
        <h1 className="text-2xl font-semibold text-slate-900 mt-1">Signals, analytics & safety</h1>
        <p className="text-slate-500 mt-2">{currentOrg.name} · source intelligence, performance learning, and controlled automation gates.</p>
      </div>
      {message && <div className="rounded-lg bg-indigo-50 text-indigo-800 px-4 py-3 text-sm">{message}</div>}

      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Signals collected</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{signals?.signal_count ?? (loading ? '…' : 0)}</p>
          <p className="text-xs text-slate-500 mt-2">Negative: {signals?.sentiments?.negative ?? 0} · Positive: {signals?.sentiments?.positive ?? 0}</p>
          <button onClick={handleCollect} className="mt-4 text-sm rounded-lg bg-indigo-600 text-white px-3 py-2 hover:bg-indigo-700">Collect trusted signals</button>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Performance snapshots</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{analytics?.metric_count ?? (loading ? '…' : 0)}</p>
          <p className="text-xs text-slate-500 mt-2">Engagements: {analytics?.totals?.engagements ?? 0} · Reach: {analytics?.totals?.reach ?? 0}</p>
        </div>
        <div className={`rounded-xl border p-5 shadow-sm ${policy?.emergency_stop ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
          <p className="text-sm text-slate-500">Automation safety</p>
          <p className="text-xl font-bold text-slate-900 mt-2">{policy?.emergency_stop ? 'EMERGENCY STOP' : policy?.approval_mode === 'controlled' ? 'CONTROLLED' : 'APPROVAL REQUIRED'}</p>
          <p className="text-xs text-slate-500 mt-2">Autopilot: {policy?.autopilot_enabled ? 'enabled' : 'disabled'} · Risk ceiling: {policy?.max_autopilot_risk_tier ?? 'low'}</p>
          <div className="flex gap-2 mt-4">
            <button onClick={policy?.emergency_stop ? handleClearStop : handleEmergencyStop} className={`text-sm rounded-lg px-3 py-2 ${policy?.emergency_stop ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}`}>
              {policy?.emergency_stop ? 'Clear stop' : 'Emergency stop'}
            </button>
            <button onClick={toggleControlledMode} className="text-sm rounded-lg border border-slate-300 px-3 py-2 text-slate-700 hover:bg-slate-50">Toggle mode</button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Top performing content</h2>
        <p className="text-sm text-slate-500 mt-1">Metrics are provider snapshots; no autonomous publishing is enabled by this screen.</p>
        <div className="mt-4 divide-y divide-slate-100">
          {(analytics?.top_content ?? []).map((item) => (
            <div key={item.content_id} className="py-3 flex items-center justify-between gap-4">
              <span className="text-sm text-slate-800">#{item.content_id} · {item.title}</span>
              <span className="text-xs text-slate-500">{item.engagements} engagements · {item.risk_tier} risk</span>
            </div>
          ))}
          {!analytics?.top_content?.length && <p className="py-4 text-sm text-slate-500">No metric snapshots have been recorded yet.</p>}
        </div>
      </div>
    </div>
  );
}
