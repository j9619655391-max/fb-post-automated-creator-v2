import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import {
  createGenerationPlan,
  listGenerationPlans,
  pauseGenerationPlan,
  resumeGenerationPlan,
  runGenerationPlanNow,
  type GenerationPlan,
} from '../api/generationPlans';

function defaultRunAt() {
  const date = new Date(Date.now() + 60 * 60 * 1000);
  date.setSeconds(0, 0);
  return date.toISOString().slice(0, 16);
}

export default function AutomationPlans() {
  const { currentOrg } = useOrg();
  const [plans, setPlans] = useState<GenerationPlan[]>([]);
  const [name, setName] = useState('Daily content draft');
  const [category, setCategory] = useState('Motivation');
  const [recurrence, setRecurrence] = useState<'daily' | 'weekly'>('daily');
  const [nextRunAt, setNextRunAt] = useState(defaultRunAt());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function refresh() {
    setLoading(true);
    try {
      setPlans(await listGenerationPlans());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load automation plans');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [currentOrg]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await createGenerationPlan({
        name,
        category_name: category || undefined,
        organization_id: currentOrg?.id,
        recurrence,
        approval_mode: 'required',
        next_run_at: new Date(nextRunAt).toISOString(),
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create automation plan');
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(plan: GenerationPlan) {
    try {
      if (plan.status === 'active') await pauseGenerationPlan(plan.id);
      else await resumeGenerationPlan(plan.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update plan');
    }
  }

  async function runNow(plan: GenerationPlan) {
    try {
      await runGenerationPlanNow(plan.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not run plan');
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Automation Plans</h1>
        <p className="text-slate-600 mt-1">Generate complete drafts on a recurring schedule. Every generated draft requires approval before publishing.</p>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <form onSubmit={handleCreate} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <h2 className="text-lg font-medium text-slate-800">Create a generation plan</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <label className="text-sm text-slate-700">
            Plan name
            <input value={name} onChange={(e) => setName(e.target.value)} required className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm text-slate-700">
            Category
            <input value={category} onChange={(e) => setCategory(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm text-slate-700">
            Recurrence
            <select value={recurrence} onChange={(e) => setRecurrence(e.target.value as 'daily' | 'weekly')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </label>
          <label className="text-sm text-slate-700">
            First run
            <input type="datetime-local" value={nextRunAt} onChange={(e) => setNextRunAt(e.target.value)} required className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
        </div>
        <button type="submit" disabled={saving} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
          {saving ? 'Creating...' : 'Create approval-required plan'}
        </button>
      </form>

      <section className="space-y-3">
        <h2 className="text-lg font-medium text-slate-800">Your plans</h2>
        {loading ? <p className="text-slate-500">Loading...</p> : plans.length === 0 ? (
          <p className="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-slate-500">No automation plans yet.</p>
        ) : plans.map((plan) => (
          <div key={plan.id} className="bg-white rounded-xl border border-slate-200 p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="font-semibold text-slate-900">{plan.name}</h3>
              <p className="text-sm text-slate-500">{plan.recurrence} · {plan.category_name || 'general'} · next run {new Date(plan.next_run_at).toLocaleString()}</p>
              <span className={`inline-block mt-2 text-xs px-2 py-1 rounded-full ${plan.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                {plan.status === 'active' ? 'Active' : 'Paused'} · approval required
              </span>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => runNow(plan)} disabled={plan.status !== 'active'} className="rounded-lg border border-indigo-300 px-3 py-2 text-sm text-indigo-700 hover:bg-indigo-50 disabled:opacity-50">Run now</button>
              <button type="button" onClick={() => changeStatus(plan)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">{plan.status === 'active' ? 'Pause' : 'Resume'}</button>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
