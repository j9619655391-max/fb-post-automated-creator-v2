import { useEffect, useState } from 'react';
import { useOrg } from '../context/OrgContext';
import { createCheckout, createPortal, getGenerationUsage, type GenerationUsageSummary } from '../api/billing';

const PLANS = [
    {
        id: 'free',
        name: 'Free',
        price: '$0',
        features: ['10 Posts / month', '1 Team Member', 'Basic Insights', 'Facebook & Instagram'],
        priceId: null
    },
    {
        id: 'pro',
        name: 'Professional',
        price: '$29',
        features: ['100 Posts / month', '5 Team Members', 'Advanced AI Tools', 'LinkedIn Integration', 'Priority Support'],
        priceId: 'price_pro_id' // This should be from config/settings in real app
    },
    {
        id: 'agency',
        name: 'Agency',
        price: '$99',
        features: ['500 Posts / month', '20 Team Members', 'Custom Export Tools', 'Multi-Workspace Management', '24/7 Dedicated Support'],
        priceId: 'price_agency_id' // This should be from config/settings in real app
    }
];

export default function Billing() {
    const { currentOrg } = useOrg();
    const [loading, setLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [usage, setUsage] = useState<GenerationUsageSummary | null>(null);

    useEffect(() => {
        if (!currentOrg) {
            setUsage(null);
            return;
        }
        getGenerationUsage(currentOrg.id)
            .then(setUsage)
            .catch(() => setUsage(null));
    }, [currentOrg]);

    const handleCheckout = async (priceId: string) => {
        if (!currentOrg) return;
        setLoading(priceId);
        setError(null);
        try {
            const { url } = await createCheckout({
                organization_id: currentOrg.id,
                price_id: priceId,
                success_url: window.location.origin + '/billing?success=true',
                cancel_url: window.location.origin + '/billing?canceled=true',
            });
            window.location.href = url;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start checkout');
            setLoading(null);
        }
    };

    const handlePortal = async () => {
        if (!currentOrg) return;
        setLoading('portal');
        setError(null);
        try {
            const { url } = await createPortal({
                organization_id: currentOrg.id,
                return_url: window.location.origin + '/billing',
            });
            window.location.href = url;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to open billing portal');
            setLoading(null);
        }
    };

    if (!currentOrg) return (
        <div className="flex items-center justify-center min-h-[60vh] text-slate-500 font-bold">
            Please select an organization to view billing information.
        </div>
    );

    return (
        <div className="max-w-6xl mx-auto px-4 py-12">
            <div className="mb-12">
                <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">Workspace Billing</h1>
                <p className="text-slate-500 font-bold">Manage your subscription and usage limits for <span className="text-indigo-600">[{currentOrg.name}]</span></p>
            </div>

            {error && (
                <div className="mb-8 p-4 bg-rose-50 border border-rose-100 rounded-2xl flex items-center gap-3 text-rose-600 font-bold text-sm shadow-sm">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-10">
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <p className="text-slate-500 text-sm font-bold">AI requests</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">{usage?.requests ?? 0}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <p className="text-slate-500 text-sm font-bold">Tokens used</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">{(usage?.total_tokens ?? 0).toLocaleString()}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <p className="text-slate-500 text-sm font-bold">Estimated AI cost</p>
                    <p className="text-2xl font-black text-indigo-600 mt-1">${(usage?.estimated_cost_usd ?? 0).toFixed(4)}</p>
                </div>
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                    <p className="text-slate-500 text-sm font-bold">Monthly AI allowance</p>
                    <p className="text-2xl font-black text-slate-900 mt-1">
                        {usage ? `${usage.ai_quota_remaining.requests.toLocaleString()} requests left` : '—'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                        {usage ? `${usage.ai_quota_remaining.tokens.toLocaleString()} tokens left` : 'Loading usage'}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                {PLANS.map((plan) => {
                    const isCurrent = currentOrg.subscription_tier === plan.id;

                    return (
                        <div key={plan.id} className={`relative p-8 rounded-[2.5rem] border ${isCurrent ? 'border-indigo-600 ring-4 ring-indigo-50 shadow-2xl shadow-indigo-100' : 'border-slate-100 hover:border-indigo-200'} bg-white transition-all duration-300 group`}>
                            {isCurrent && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg">
                                    Current Plan
                                </div>
                            )}

                            <div className="mb-8">
                                <h3 className="text-xl font-black text-slate-900 mb-2">{plan.name}</h3>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-4xl font-black text-slate-900 tracking-tighter">{plan.price}</span>
                                    <span className="text-sm font-bold text-slate-400">/mo</span>
                                </div>
                            </div>

                            <ul className="space-y-4 mb-10">
                                {plan.features.map((feat, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm font-bold text-slate-600">
                                        <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center ${isCurrent ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-50 text-slate-400'}`}>
                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /></svg>
                                        </div>
                                        {feat}
                                    </li>
                                ))}
                            </ul>

                            {plan.priceId && (
                                <button
                                    onClick={() => handleCheckout(plan.priceId!)}
                                    disabled={loading !== null || isCurrent}
                                    className={`w-full py-4 rounded-2xl font-black text-sm tracking-tight transition-all duration-300 ${isCurrent
                                        ? 'bg-slate-50 text-slate-400 cursor-default'
                                        : 'bg-indigo-600 text-white shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:-translate-y-1 active:translate-y-0 disabled:opacity-50'
                                        }`}
                                >
                                    {loading === plan.priceId ? (
                                        <div className="flex items-center justify-center gap-2">
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            Processing...
                                        </div>
                                    ) : isCurrent ? 'Active Subscription' : 'Upgrade Workspace'}
                                </button>
                            )}
                            {!plan.priceId && (
                                <div className="w-full py-4 text-center rounded-2xl bg-slate-50 text-slate-400 font-black text-sm uppercase tracking-widest">
                                    Baseline
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="p-10 rounded-[3rem] bg-slate-900 text-white shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl"></div>
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
                    <div>
                        <h2 className="text-2xl font-black mb-2 tracking-tight">Need custom billing or more seats?</h2>
                        <p className="text-slate-400 font-bold max-w-lg">Manage your invoices, payment methods, and account history through our secure Stripe portal.</p>
                    </div>
                    <button
                        onClick={handlePortal}
                        disabled={loading !== null || !currentOrg.stripe_customer_id}
                        className="px-10 py-5 bg-white text-slate-900 rounded-3xl font-black text-sm tracking-tight transition-all duration-300 hover:bg-slate-100 hover:shadow-xl active:scale-95 disabled:opacity-30 flex items-center gap-3 group"
                    >
                        {loading === 'portal' ? (
                            <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-900 rounded-full animate-spin"></div>
                        ) : (
                            <svg className="w-5 h-5 text-indigo-600 transition-transform group-hover:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                        )}
                        Manage Billing Portal
                    </button>
                    {!currentOrg.stripe_customer_id && (
                        <p className="text-[10px] font-bold text-slate-500 mt-2 md:mt-0 uppercase tracking-widest">Subscribe to a plan to enable portal</p>
                    )}
                </div>
            </div>
        </div>
    );
}
