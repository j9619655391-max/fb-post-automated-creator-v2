import { Link, useLocation, Outlet, useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useOrg } from '../context/OrgContext';
import OrganizationSwitcher from './OrganizationSwitcher';

export default function Layout() {
  const { isAuthenticated, user, logout, isLoading } = useAuth();
  const { isPro, isAgency } = useOrg();
  const location = useLocation();
  const navigate = useNavigate();

  // Redirect if not authenticated (handled by RequireAuth, but safe for layout)
  if (!isAuthenticated && location.pathname !== '/login' && location.pathname !== '/signup') {
    return <Navigate to="/login" replace />;
  }

  if (isAuthenticated && !user && isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-500">Loading...</p>
      </div>
    );
  }

  const isLogin = location.pathname === '/login';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto w-full min-w-0 px-4 py-4 flex flex-col gap-3">
          <div className="flex w-full min-w-0 items-center justify-between gap-4">
            <Link to="/" className="font-black text-xl tracking-tighter text-slate-900 flex items-center gap-2 flex-shrink-0">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              </div>
              <span className="hidden sm:inline">AUTOGROWTH</span>
            </Link>

            {!isLogin && location.pathname !== '/signup' && (
              <div className="max-w-xs w-full hidden md:block">
                <OrganizationSwitcher />
              </div>
            )}
          </div>
          {!isLogin && location.pathname !== '/signup' && (
            <nav className="flex w-full min-w-0 flex-wrap items-center gap-1 border-t border-slate-100 pt-3">
              {[
                { to: '/', label: 'DASHBOARD' },
                { to: '/calendar', label: 'SCHEDULER' },
                { to: '/automation-plans', label: 'AUTOPILOT' },
                { to: '/content', label: 'PRODUCTION' },
                                { to: '/insights', label: 'ANALYTICS' },
                { to: '/roadmap-controls', label: 'OPERATIONS' },
                { to: '/creative-studio', label: 'STUDIO' },

                { to: '/platforms', label: 'NETWORK' },
                                { to: '/organizations', label: 'WORKSPACE' },
                { to: '/workspace-intelligence', label: 'KNOWLEDGE' },
                { to: '/billing', label: 'BILLING' }

              ].map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${location.pathname === link.to || (link.to !== '/' && location.pathname.startsWith(link.to))
                    ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                    : 'text-slate-500 hover:text-indigo-600 hover:bg-slate-50'
                    }`}
                >
                  {link.label}
                </Link>
              ))}

              {user?.is_admin && (
                <Link
                  to="/system-settings"
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${location.pathname.startsWith('/system-settings')
                    ? 'bg-rose-50 text-rose-700 shadow-sm'
                    : 'text-rose-500 hover:text-rose-600 hover:bg-rose-50'
                    }`}
                >
                  SYSTEM SETTINGS
                </Link>
              )}

              <div className="h-6 w-px bg-slate-200 mx-2"></div>

              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end">
                  <span className="text-[10px] font-black text-slate-900 leading-none">
                    {user?.username.toUpperCase()}
                  </span>
                  <span className={`text-[8px] font-black uppercase tracking-tighter px-1.5 py-0.5 rounded ${isAgency ? 'bg-amber-100 text-amber-700' :
                    isPro ? 'bg-indigo-100 text-indigo-700' :
                      'bg-slate-100 text-slate-400'
                    }`}>
                    {isAgency ? 'AGENCY' : isPro ? 'PRO' : 'FREE'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => { logout(); navigate('/login'); }}
                  className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                  title="Logout"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                </button>
              </div>
            </nav>
          )}
        </div>
      </header>
      <main className="flex-1 min-w-0 max-w-7xl w-full mx-auto px-4 py-8 overflow-x-clip">
        <Outlet />
      </main>
    </div>
  );
}
