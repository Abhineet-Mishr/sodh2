
import { useAuth } from '../context/AuthContext';
import { Database, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-10">
        <h2 className="text-3xl font-bold text-gray-900">Welcome, {user?.email}</h2>
        <p className="text-gray-600 mt-2">What would you like to research today?</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">

        {/* Deep Explore Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-md transition-shadow">
          <div className="bg-brand-lavender/30 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
            <Database size={32} className="text-brand-primary" />
          </div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-3">Deep Explore</h3>
          <p className="text-gray-600 mb-8 min-h-[80px]">
            Generate literature-backed research insights by analyzing published studies. Identify research gaps and build evidence-backed proposals.
          </p>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-brand-primary bg-brand-light px-3 py-1 rounded-full">
              Costs 10+ Credits
            </span>
            <Link
              to="/deep-explore"
              className="text-white bg-brand-primary hover:bg-brand-dark px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Launch
            </Link>
          </div>
        </div>

        {/* Search Builder Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-md transition-shadow">
          <div className="bg-brand-lavender/30 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
            <Search size={32} className="text-brand-primary" />
          </div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-3">Search Builder</h3>
          <p className="text-gray-600 mb-8 min-h-[80px]">
            Quickly generate optimized Boolean search queries for PubMed, Scopus, and Embase using our AI model.
          </p>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-brand-primary bg-brand-light px-3 py-1 rounded-full">
              Free Utility
            </span>
            <Link
              to="/search-builder"
              className="text-brand-primary border-2 border-brand-primary hover:bg-brand-primary hover:text-white px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Launch
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
