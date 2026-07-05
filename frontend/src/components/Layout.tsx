
import { Link, useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BrainCircuit, Search, Database, LogOut, User } from 'lucide-react';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: BrainCircuit },
    { name: 'Deep Explore', path: '/deep-explore', icon: Database },
    { name: 'Search Builder', path: '/search-builder', icon: Search },
  ];

  return (
    <div className="flex h-screen bg-brand-light">
      {/* Sidebar */}
      <div className="w-64 gradient-bg text-white shadow-xl flex flex-col">
        <div className="p-6 flex items-center space-x-3">
          <BrainCircuit size={28} className="text-brand-lavender" />
          <span className="text-2xl font-bold tracking-wider">SODH OS</span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-white/20 text-white font-medium'
                    : 'text-brand-lavender hover:bg-white/10 hover:text-white'
                }`}
              >
                <item.icon size={20} />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {user && (
          <div className="p-4 border-t border-white/20">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-brand-lavender/20 p-2 rounded-full">
                <User size={20} className="text-brand-lavender" />
              </div>
              <div>
                <p className="text-sm font-medium text-white truncate max-w-[140px]">{user.email}</p>
                <p className="text-xs text-brand-lavender flex items-center mt-1">
                  <span className="inline-block w-2 h-2 rounded-full bg-green-400 mr-2"></span>
                  {user.credits} Credits
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center space-x-2 text-sm text-brand-lavender hover:text-white transition-colors"
            >
              <LogOut size={16} />
              <span>Log out</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white shadow-sm border-b border-gray-100">
          <div className="px-8 py-4 flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-800">
              {navItems.find(i => location.pathname === i.path || (i.path !== '/' && location.pathname.startsWith(i.path)))?.name || 'SODH Workspace'}
            </h1>
          </div>
        </header>
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
