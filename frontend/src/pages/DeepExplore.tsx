import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Database, Loader2, FileText, AlertCircle, RefreshCw } from 'lucide-react';

const DeepExplore: React.FC = () => {
  const { user, refreshUser } = useAuth();

  const [topic, setTopic] = useState('');
  const [paperLimit, setPaperLimit] = useState(100);

  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const calculateCost = (limit: number) => {
    if (limit >= 300) return 20;
    if (limit >= 200) return 15;
    return 10;
  };

  const handleStartJob = async (e: React.FormEvent) => {
    e.preventDefault();
    const cost = calculateCost(paperLimit);
    if (user && user.credits < cost) {
      setError(`Insufficient credits. You need ${cost} credits but have ${user.credits}.`);
      return;
    }

    setLoading(true);
    setError('');
    setReport(null);
    setJobStatus('Queued');

    try {
      const res = await api.post('/deep-explore/', { topic, paper_limit: paperLimit });
      setJobId(res.data.job_id);
      refreshUser(); // Updates credit count immediately after reservation
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start Deep Explore job.');
      setLoading(false);
      setJobStatus(null);
    }
  };

  // Polling logic
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (jobId && jobStatus && !['COMPLETED', 'FAILED', 'CANCELLED'].includes(jobStatus)) {
      intervalId = setInterval(async () => {
        try {
          // Since we didn't expose a GET /deep-explore/{job_id} endpoint in the backend implementation yet,
          // we need to add it to the backend or simulate it here.

          const res = await api.get(`/deep-explore/${jobId}`);
          setJobStatus(res.data.status);

          if (res.data.status === 'COMPLETED' && res.data.report) {
            setReport(res.data.report);
            setLoading(false);
          } else if (res.data.status === 'FAILED') {
            setError('Job failed during processing. Credits have been refunded.');
            setLoading(false);
            refreshUser();
          }
        } catch (err) {
          console.error("Error polling job status:", err);
        }
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, jobStatus]);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Deep Explore</h2>
        <p className="text-gray-600">
          Generate literature-backed research insights by analyzing published studies.
        </p>
      </div>

      {!jobId || ['FAILED', 'CANCELLED'].includes(jobStatus || '') ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 mb-8">
          <form onSubmit={handleStartJob} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Research Topic <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Acute ischemic stroke magnesium"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-accent outline-none"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Literature Search Limit
              </label>
              <select
                value={paperLimit}
                onChange={(e) => setPaperLimit(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-accent outline-none bg-white"
              >
                <option value={100}>Top 100 Papers (10 Credits)</option>
                <option value={200}>Top 200 Papers (15 Credits)</option>
                <option value={300}>Top 300 Papers (20 Credits)</option>
              </select>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-start space-x-3">
                <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={loading || !topic}
                className="gradient-bg text-white px-8 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center space-x-2 disabled:opacity-50"
              >
                <Database size={18} />
                <span>Start Deep Explore Job</span>
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Job Status Banner */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
                {jobStatus === 'COMPLETED' ? (
                  <><FileText size={20} className="text-brand-primary" /> <span>Report Generated</span></>
                ) : (
                  <><Loader2 size={20} className="text-brand-accent animate-spin" /> <span>Processing Research Topic</span></>
                )}
              </h3>
              <p className="text-sm text-gray-500 mt-1">Job ID: {jobId}</p>
            </div>

            <div className="text-right">
              <div className="inline-block px-4 py-1.5 rounded-full text-sm font-medium border border-brand-lavender bg-brand-light text-brand-primary">
                Status: {jobStatus?.replace('_', ' ')}
              </div>
            </div>
          </div>

          {/* Render Report if complete */}
          {report && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-4 border-b pb-4">Executive Summary</h3>
                <p className="text-gray-700 leading-relaxed">{report.executive_summary}</p>
              </div>

              {report.top_research_gaps && report.top_research_gaps.length > 0 && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                  <h3 className="text-xl font-bold text-gray-900 mb-6">Top Research Gaps</h3>
                  <div className="grid gap-4">
                    {report.top_research_gaps.map((gap: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl border border-gray-100 bg-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                          <p className="font-medium text-gray-900">{gap.title}</p>
                          <p className="text-xs text-gray-500 mt-1 font-mono">Cluster ID: {gap.cluster_id}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold
                          ${gap.confidence === 'High' ? 'bg-green-100 text-green-700' :
                            gap.confidence === 'Moderate' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'}`}>
                          {gap.confidence} Confidence
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Other sections can be mapped out similarly */}
              <div className="grid md:grid-cols-2 gap-6">
                {['future_studies', 'srma_topics', 'methodological_limitations', 'underrepresented_populations'].map((sectionKey) => {
                  if (!report[sectionKey] || report[sectionKey].length === 0) return null;
                  return (
                    <div key={sectionKey} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 capitalize">
                        {sectionKey.replace('_', ' ')}
                      </h3>
                      <ul className="list-disc pl-5 space-y-2 text-gray-700">
                        {report[sectionKey].map((item: string, idx: number) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-center pt-8">
                 <button onClick={() => { setJobId(null); setJobStatus(null); setTopic(''); }} className="text-brand-primary font-medium hover:underline flex items-center space-x-2">
                   <RefreshCw size={18} />
                   <span>Start a New Deep Explore</span>
                 </button>
              </div>

            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DeepExplore;
