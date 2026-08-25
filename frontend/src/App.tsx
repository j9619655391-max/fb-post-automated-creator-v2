import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { OrgProvider } from './context/OrgContext'; // Added OrgProvider import
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ContentList from './pages/ContentList';
import ContentForm from './pages/ContentForm';
import ContentDetail from './pages/ContentDetail';
import MetaPages from './pages/MetaPages';
import AuditLogs from './pages/AuditLogs';
import Users from './pages/Users';
import Insights from './pages/Insights';
import Calendar from './pages/Calendar';
import Signup from './pages/Signup';
import Platforms from './pages/Platforms';
import Organizations from './pages/Organizations';
import Billing from './pages/Billing';
import SystemSettings from './pages/SystemSettings';
import AutomationPlans from './pages/AutomationPlans';
import WorkspaceIntelligence from './pages/WorkspaceIntelligence';
import RoadmapControls from './pages/RoadmapControls';
import CreativeStudio from './pages/CreativeStudio';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user?.is_admin) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-2xl font-semibold text-slate-900">Administrator access required</h1>
        <p className="mt-3 text-slate-600">System Settings is limited to platform administrators.</p>
      </div>
    );
  }
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="content" element={<ContentList />} />
        <Route path="content/new" element={<ContentForm />} />
        <Route path="content/:id" element={<ContentDetail />} />
        <Route path="content/:id/edit" element={<ContentForm />} />
        <Route path="meta-pages" element={<MetaPages />} />
        <Route path="platforms" element={<Platforms />} />
                <Route path="organizations" element={<Organizations />} />
        <Route path="workspace-intelligence" element={<WorkspaceIntelligence />} />
        <Route path="roadmap-controls" element={<RoadmapControls />} />
        <Route path="creative-studio" element={<CreativeStudio />} />

        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="users" element={<Users />} />
        <Route path="insights" element={<Insights />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="automation-plans" element={<AutomationPlans />} />
        <Route path="billing" element={<Billing />} />
        <Route path="system-settings" element={<RequireAdmin><SystemSettings /></RequireAdmin>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <OrgProvider>
          <AppRoutes />
        </OrgProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
