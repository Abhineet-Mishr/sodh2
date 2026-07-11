import React, { useState } from 'react';
import { ResearchSuggestionRequest } from './types';

interface Props {
  onSubmit: (request: ResearchSuggestionRequest) => void;
  isLoading: boolean;
}

export const ResearchSuggestionForm: React.FC<Props> = ({ onSubmit, isLoading }) => {
  const [topic, setTopic] = useState('');
  const [purpose, setPurpose] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit({ topic, purpose: purpose || 'General brainstorming' });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Generate Research Suggestions</h2>

      <div className="mb-4">
        <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-1">
          Research Topic <span className="text-red-500">*</span>
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., Serum magnesium and acute ischemic stroke"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
          required
        />
      </div>

      <div className="mb-6">
        <label htmlFor="purpose" className="block text-sm font-medium text-gray-700 mb-1">
          Purpose (Optional)
        </label>
        <input
          id="purpose"
          type="text"
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          placeholder="e.g., Finding novel biomarkers for a PhD thesis"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
      </div>

      <button
        type="submit"
        disabled={isLoading || !topic.trim()}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {isLoading ? 'Generating... (Takes ~5-15 seconds)' : 'Generate Ideas (Costs 5 Credits)'}
      </button>
    </form>
  );
};
