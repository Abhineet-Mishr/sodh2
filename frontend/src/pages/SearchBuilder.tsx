import { useState } from 'react';
import { Search, Loader2, Copy, Check } from 'lucide-react';
import api from '../lib/api';

interface SearchQueries {
  pubmed_query: string;
  scopus_query: string;
  embase_query: string;
}

const SearchBuilder: React.FC = () => {
  const [topic, setTopic] = useState('');
  const [studyType, setStudyType] = useState('');
  const [purpose, setPurpose] = useState('');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchQueries | null>(null);
  const [error, setError] = useState('');

  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await api.post('/literature/search-builder', {
        topic,
        study_type: studyType || undefined,
        purpose: purpose || undefined
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate search queries.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Search Builder</h2>
        <p className="text-gray-600">
          Generate optimized Boolean queries for PubMed, Scopus, and Embase using AI.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Research Topic <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Serum magnesium and acute ischemic stroke"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-accent outline-none"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Study Type (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Randomized Controlled Trial"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-accent outline-none"
                value={studyType}
                onChange={(e) => setStudyType(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Purpose (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Systematic Review"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-accent outline-none"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !topic}
              className="gradient-bg text-white px-6 py-2.5 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center space-x-2 disabled:opacity-50"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
              <span>Generate Queries</span>
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-8 border border-red-100">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 border-b pb-2">Generated Queries</h3>

          {[
            { key: 'pubmed_query', title: 'PubMed' },
            { key: 'scopus_query', title: 'Scopus' },
            { key: 'embase_query', title: 'Embase' }
          ].map((item) => (
            <div key={item.key} className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                <span className="font-semibold text-gray-800">{item.title}</span>
                <button
                  onClick={() => handleCopy((result as any)[item.key], item.key)}
                  className="text-gray-500 hover:text-brand-primary transition-colors flex items-center space-x-1 text-sm"
                >
                  {copied === item.key ? (
                    <><Check size={16} className="text-green-500"/> <span className="text-green-500">Copied!</span></>
                  ) : (
                    <><Copy size={16} /> <span>Copy</span></>
                  )}
                </button>
              </div>
              <div className="p-4 text-gray-700 font-mono text-sm leading-relaxed overflow-x-auto">
                {(result as any)[item.key]}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBuilder;
