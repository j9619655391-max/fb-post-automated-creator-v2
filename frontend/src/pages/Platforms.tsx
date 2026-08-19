import { useEffect, useState } from 'react';
import { apiPost } from '../api/client';
import type { PlatformStatus } from '../api/platforms';
import { getPlatformsStatus, syncLinkedInAccounts } from '../api/platforms';

export default function Platforms() {
    const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [syncing, setSyncing] = useState(false);
    const [connecting, setConnecting] = useState(false);

    const fetchStatus = async () => {
        try {
            const data = await getPlatformsStatus();
            setPlatforms(data);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch platform status');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const initiateOAuth = async (provider: 'facebook' | 'linkedin') => {
        setConnecting(true);
        setError(null);
        try {
            const result = await apiPost<{ authorize_url: string }>(`auth/${provider}/login`);
            window.location.assign(result.authorize_url);
        } catch (err: any) {
            setError(err.message || `Failed to start ${provider} connection`);
            setConnecting(false);
        }
    };

    const handleConnectFacebook = () => initiateOAuth('facebook');
    const handleConnectLinkedIn = () => initiateOAuth('linkedin');

    const handleSyncLinkedIn = async () => {
        setSyncing(true);
        try {
            await syncLinkedInAccounts();
            await fetchStatus();
            alert('LinkedIn accounts synced successfully!');
        } catch (err: any) {
            alert(`Sync failed: ${err.message}`);
        } finally {
            setSyncing(false);
        }
    };

    if (loading) return <div className="text-center py-10">Loading platform status...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900">Social Platforms</h1>
            </div>

            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded-md border border-red-100">
                    {error}
                </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                {/* Facebook Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs">FB</span>
                            Facebook
                        </h2>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${platforms.find(p => p.platform === 'facebook')?.connected
                            ? 'bg-green-100 text-green-700'
                            : 'bg-slate-100 text-slate-700'
                            }`}>
                            {platforms.find(p => p.platform === 'facebook')?.connected ? 'Connected' : 'Not Connected'}
                        </span>
                    </div>

                    <p className="text-slate-600 text-sm mb-6">
                        Connect your Facebook account to manage pages and publish posts.
                    </p>

                    <div className="space-y-4">
                        {platforms.find(p => p.platform === 'facebook')?.connected ? (
                            <div className="flex flex-col gap-2">
                                <div className="text-sm text-slate-500">
                                    {platforms.find(p => p.platform === 'facebook')?.accounts_count} Pages matched
                                </div>
                                <button
                                    onClick={handleConnectFacebook}
                                    disabled={connecting}
                                    className="w-full py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                                >
                                    Reconnect / Change Pages
                                </button>
                                <a
                                    href="/meta-pages"
                                    className="text-center py-2 text-blue-600 hover:underline text-sm font-medium"
                                >
                                    Manage Facebook Pages
                                </a>
                            </div>
                        ) : (
                            <button
                                onClick={handleConnectFacebook}
                                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                                Connect Facebook
                            </button>
                        )}
                    </div>
                </div>

                {/* LinkedIn Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <span className="w-8 h-8 bg-blue-800 text-white rounded-full flex items-center justify-center text-xs">IN</span>
                            LinkedIn
                        </h2>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${platforms.find(p => p.platform === 'linkedin')?.connected
                            ? 'bg-green-100 text-green-700'
                            : 'bg-slate-100 text-slate-700'
                            }`}>
                            {platforms.find(p => p.platform === 'linkedin')?.connected ? 'Connected' : 'Not Connected'}
                        </span>
                    </div>

                    <p className="text-slate-600 text-sm mb-6">
                        Connect your LinkedIn profile to publish professional content updates.
                    </p>

                    <div className="space-y-4">
                        {platforms.find(p => p.platform === 'linkedin')?.connected ? (
                            <div className="flex flex-col gap-2">
                                <div className="text-sm text-slate-500">
                                    {platforms.find(p => p.platform === 'linkedin')?.accounts_count} Profiles/Pages found
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSyncLinkedIn}
                                        disabled={syncing}
                                        className="flex-1 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors text-sm font-medium"
                                    >
                                        {syncing ? 'Syncing...' : 'Sync Accounts'}
                                    </button>
                                    <button
                                        onClick={handleConnectLinkedIn}
                                        disabled={connecting}
                                        className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
                                    >
                                        Reconnect
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={handleConnectLinkedIn}
                                className="w-full py-2 bg-blue-800 text-white rounded-lg hover:bg-blue-900 transition-colors text-sm font-medium"
                            >
                                Connect LinkedIn
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
