import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export const Header = () => {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <header className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
      <Link to="/dashboard" className="text-xl font-bold tracking-wide">
        WATO Clusters - DNA Analysis
      </Link>
      {isAuthenticated && (
        <div className="flex items-center gap-4">
          <span className="text-gray-300 text-sm">{user?.email}</span>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 text-white text-sm px-3 py-1.5 rounded"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
};
