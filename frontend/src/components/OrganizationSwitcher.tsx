import { useOrg } from '../context/OrgContext';
import { Link } from 'react-router-dom';

export default function OrganizationSwitcher() {
    const { organizations, currentOrg, setCurrentOrg, isLoading } = useOrg();

    if (isLoading) return <div className="text-[10px] text-slate-400 animate-pulse">Loading Orgs...</div>;

    return (
        <div className="flex flex-col gap-1 w-full">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">Active Workspace</span>
                <Link to="/organizations" className="text-[9px] font-black text-indigo-600 uppercase tracking-widest hover:underline">
                    Manage
                </Link>
            </div>

            <div className="relative group">
                <select
                    value={currentOrg?.id || ''}
                    onChange={(e) => {
                        const org = organizations.find(o => o.id === parseInt(e.target.value));
                                                if (org) {
                            window.localStorage.setItem('active_org_id', String(org.id));
                            setCurrentOrg(org);
                        }

                    }}
                    className="w-full bg-slate-50 border-slate-200 text-slate-900 text-xs font-black rounded-xl py-2.5 pl-4 pr-10 appearance-none focus:ring-2 focus:ring-indigo-100 transition-all cursor-pointer group-hover:bg-white group-hover:border-indigo-200"
                >
                    {organizations.map(org => (
                        <option key={org.id} value={org.id}>
                            {org.name.toUpperCase()}
                        </option>
                    ))}
                    {organizations.length === 0 && (
                        <option value="" disabled>NO WORKSPACES</option>
                    )}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 transition-transform group-hover:scale-110">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </div>

            {currentOrg && (
                <div className="mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-100">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
                    <span className="text-[9px] font-black text-indigo-700 uppercase tracking-widest truncate">
                        {currentOrg.slug}
                    </span>
                </div>
            )}
        </div>
    );
}
