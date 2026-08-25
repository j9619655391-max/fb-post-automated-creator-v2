import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { listUsers, type User } from '../api/users';

export default function Users() {
  const { isAuthenticated, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      setLoading(false);
      return;
    }
    listUsers()
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [isAuthenticated, user?.is_admin]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Users</h1>
      {!user?.is_admin ? (
        <div className="bg-amber-50 rounded-xl border border-amber-200 p-8 text-center text-amber-800">
          User management is available to platform administrators only.
        </div>
      ) : loading ? (
        <p className="text-slate-500">Loading...</p>
      ) : users.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
          No users.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-700">ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-700">Username</th>
                <th className="text-left px-4 py-3 font-medium text-slate-700">Email</th>
                <th className="text-left px-4 py-3 font-medium text-slate-700">Role</th>
                <th className="text-left px-4 py-3 font-medium text-slate-700">Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">{u.id}</td>
                  <td className="px-4 py-3 font-medium">{u.username}</td>
                  <td className="px-4 py-3 text-slate-600">{u.email}</td>
                  <td className="px-4 py-3">{u.is_admin ? 'Admin' : 'User'}</td>
                  <td className="px-4 py-3">{u.is_active ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
