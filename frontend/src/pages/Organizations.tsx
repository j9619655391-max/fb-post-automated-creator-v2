import { useState, useEffect, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useOrg } from '../context/OrgContext';
import {
    createOrganization,
    listOrgMembers,
    addOrgMember,
    removeOrgMember,
    type OrgMember,
    type OrganizationRole
} from '../api/organizations';

export default function Organizations() {
    const { user } = useAuth();
    const { organizations, currentOrg, setCurrentOrg, refreshOrganizations } = useOrg();

    const [members, setMembers] = useState<OrgMember[]>([]);
    const [loadingMembers, setLoadingMembers] = useState(false);
    const [newMemberEmail, setNewMemberEmail] = useState('');
    const [newMemberRole, setNewMemberRole] = useState<OrganizationRole>('member');

    const [newOrgName, setNewOrgName] = useState('');
    const [newOrgSlug, setNewOrgSlug] = useState('');
    const [error, setError] = useState('');
const [success, setSuccess] = useState('');

    const managementLinks = [
        { to: '/workspace-intelligence', label: 'Knowledge & sources', description: 'Review workspace context, evidence, and approved source grounding.', tone: 'bg-indigo-50 text-indigo-700 border-indigo-100' },
        { to: '/creative-studio', label: 'Brand & templates', description: 'Compose branded image packages and inspect draft previews.', tone: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-100' },
        { to: '/roadmap-controls', label: 'Safety & approval', description: 'Review approval-required mode, risk controls, and operations status.', tone: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
        { to: '/platforms', label: 'Channels & readiness', description: 'Inspect provider connection state without initiating OAuth.', tone: 'bg-amber-50 text-amber-700 border-amber-100' },
        { to: '/billing', label: 'Usage & plan', description: 'Monitor AI request usage, token consumption, and plan limits.', tone: 'bg-sky-50 text-sky-700 border-sky-100' },
        { to: '/audit-logs', label: 'Audit trail', description: 'Review generation, approval, scheduling, and provider events.', tone: 'bg-slate-100 text-slate-700 border-slate-200' },
    ];

    useEffect(() => {
        if (currentOrg) {
            loadMembers(currentOrg.id);
        } else {
            setMembers([]);
        }
    }, [currentOrg]);

    async function loadMembers(orgId: number) {
        setLoadingMembers(true);
        try {
            const data = await listOrgMembers(orgId);
            setMembers(data);
        } catch (err) {
            console.error('Failed to load members', err);
        } finally {
            setLoadingMembers(false);
        }
    }

    async function handleCreateOrg(e: FormEvent) {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            await createOrganization(newOrgName, newOrgSlug);
            setSuccess('Organization created successfully!');
            setNewOrgName('');
            setNewOrgSlug('');
            await refreshOrganizations();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create organization');
        }

    }

    async function handleAddMember(e: FormEvent) {
        e.preventDefault();
        if (!currentOrg) return;
        setError('');
        setSuccess('');
        try {
            await addOrgMember(currentOrg.id, newMemberEmail, newMemberRole);
            setSuccess('Member invited successfully!');
            setNewMemberEmail('');
            loadMembers(currentOrg.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add member');
        }

    }

    async function handleRemoveMember(userId: number) {
        if (!currentOrg || !window.confirm('Are you sure you want to remove this member?')) return;
        try {
            await removeOrgMember(currentOrg.id, userId);
            loadMembers(currentOrg.id);
            setSuccess('Member removed');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to remove member');
        }

    }

    return (
        <div className="space-y-8">
            <header>
<h1 className="text-2xl font-semibold text-slate-900">Manage workspace</h1>
                <p className="text-slate-600">Control workspace identity, content intelligence, brand templates, safety, channels, usage, and team access from one place.</p>
                        </header>

            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Workspace management shortcuts">
                {managementLinks.map((link) => (
                    <Link key={link.to} to={link.to} className={`rounded-2xl border p-4 transition-shadow hover:shadow-md ${link.tone}`}>
                        <div className="mb-1 flex items-center justify-between gap-3">
                            <h2 className="text-sm font-bold">{link.label}</h2>
                            <span aria-hidden="true">→</span>
                        </div>
                        <p className="text-xs leading-relaxed opacity-80">{link.description}</p>
                    </Link>
                ))}
            </section>

            <div className="rounded-xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
                <strong>Safety contract:</strong> drafts remain local and unpublished until the existing human approval workflow is completed. This management panel does not connect providers, publish, schedule, send Telegram messages, or change emergency-stop controls by itself.
            </div>

            {error && <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100">{error}</div>}
            {success && <div className="p-4 bg-emerald-50 text-emerald-700 rounded-lg text-sm border border-emerald-100">{success}</div>}

            <div className="grid md:grid-cols-3 gap-8">
                {/* Left: Organization Switcher & Creation */}
                <div className="md:col-span-1 space-y-6">
                    <section className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h2 className="text-sm font-semibold text-slate-800 mb-4 uppercase tracking-wider">Your Workspaces</h2>
                        <div className="space-y-2">
                            {organizations.map(org => (
                                <button
                                    key={org.id}
                                    onClick={() => setCurrentOrg(org)}
                                    className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${currentOrg?.id === org.id
                                        ? 'bg-indigo-50 border-indigo-200 text-indigo-700 shadow-sm'
                                        : 'bg-white border-slate-100 text-slate-600 hover:border-slate-300'
                                        }`}
                                >
                                    <div className="font-semibold">{org.name}</div>
                                    <div className="text-[10px] opacity-70 uppercase tracking-tight">ID: {org.slug}</div>
                                </button>
                            ))}
                            {organizations.length === 0 && (
                                <p className="text-slate-400 text-sm italic py-4 text-center">No team workspaces yet.</p>
                            )}
                        </div>
                    </section>

                    <section className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
                        <h2 className="text-sm font-semibold text-slate-800 mb-4">Create New Workspace</h2>
                        <form onSubmit={handleCreateOrg} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Company Name</label>
                                <input
                                    type="text"
                                    required
                                    className="w-full rounded-lg border-slate-200 text-sm"
                                    value={newOrgName}
                                    onChange={e => {
                                        setNewOrgName(e.target.value);
                                        setNewOrgSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '-'));
                                    }}
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">URL Identifier (slug)</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="my-team"
                                    className="w-full rounded-lg border-slate-200 text-sm"
                                    value={newOrgSlug}
                                    onChange={e => setNewOrgSlug(e.target.value)}
                                />
                            </div>
                            <button type="submit" className="w-full py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition-colors">
                                Create Workspace
                            </button>
                        </form>
                    </section>
                </div>

                {/* Right: Member Management */}
                <div className="md:col-span-2 space-y-6">
                    {currentOrg ? (
                        <>
                            <section className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h2 className="text-xl font-bold text-slate-900">{currentOrg.name} Members</h2>
                                        <p className="text-slate-500 text-sm">Manage who has access to this workspace.</p>
                                    </div>
                                    <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded-full uppercase tracking-widest">
                                        Active Org
                                    </span>
                                </div>

                                <div className="overflow-hidden rounded-xl border border-slate-100">
                                    <table className="w-full text-left text-sm">
                                        <thead className="bg-slate-50">
                                            <tr>
                                                <th className="px-6 py-3 font-semibold text-slate-700">User</th>
                                                <th className="px-6 py-3 font-semibold text-slate-700">Role</th>
                                                <th className="px-6 py-3 font-semibold text-slate-700 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {members.map(member => (
                                                <tr key={member.id} className="hover:bg-slate-50/50 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div className="font-medium text-slate-900">{member.username}</div>
                                                        <div className="text-[10px] text-slate-400 lowercase">Joined {new Date(member.joined_at).toLocaleDateString()}</div>
                                                    </td>
                                                    <td className="px-6 py-4 lowercase italic">
                                                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${member.role === 'owner' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                                                            }`}>
                                                            {member.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        {member.user_id !== user?.id && member.role !== 'owner' && (
                                                            <button
                                                                onClick={() => handleRemoveMember(member.user_id)}
                                                                className="text-red-500 hover:text-red-700 text-xs font-semibold"
                                                            >
                                                                Remove
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                            {loadingMembers && (
                                                <tr><td colSpan={3} className="px-6 py-8 text-center text-slate-400">Loading members...</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </section>

                            <section className="bg-indigo-900 p-8 rounded-2xl text-white shadow-xl shadow-indigo-100 relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 blur-3xl rounded-full -mr-16 -mt-16"></div>
                                <h3 className="text-lg font-bold mb-4">Invite Team Member</h3>
                                <form onSubmit={handleAddMember} className="grid md:grid-cols-4 gap-4">
                                    <div className="md:col-span-2">
                                        <label className="block text-[10px] font-bold uppercase tracking-widest text-indigo-200 mb-1">Email Address</label>
                                        <input
                                            type="email"
                                            required
                                            placeholder="colleague@company.com"
                                            className="w-full rounded-lg border-indigo-700 bg-indigo-800 text-white placeholder-indigo-400 text-sm focus:ring-2 focus:ring-white/20"
                                            value={newMemberEmail}
                                            onChange={e => setNewMemberEmail(e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold uppercase tracking-widest text-indigo-200 mb-1">Role</label>
                                        <select
                                            className="w-full rounded-lg border-indigo-700 bg-indigo-800 text-white text-sm"
                                            value={newMemberRole}
                                            onChange={e => setNewMemberRole(e.target.value as OrganizationRole)}
                                        >
                                            <option value="member">Member</option>
                                            <option value="admin">Admin</option>
                                            <option value="editor">Editor</option>
                                        </select>
                                    </div>
                                    <div className="flex items-end">
                                        <button type="submit" className="w-full py-2 bg-white text-indigo-900 rounded-lg text-sm font-black uppercase hover:bg-slate-100 transition-colors">
                                            Send Invite
                                        </button>
                                    </div>
                                </form>
                            </section>
                        </>
                    ) : (
                        <div className="h-96 flex flex-col items-center justify-center bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200 text-center p-12">
                            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm mb-6">
                                <svg className="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-2">Select a Workspace</h3>
                            <p className="text-slate-500 max-w-sm mb-8">Choose an organization from the left to manage members and collaborative settings.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
