import { ResearchSuggestionForm } from './components/ResearchSuggestionForm';
import { ResearchSuggestionResults } from './components/ResearchSuggestionResults';
import { useResearchSuggestions } from './hooks/useResearchSuggestions';

export const ResearchSuggestionsPage = () => {
  const { data, isLoading, error, generateSuggestions } = useResearchSuggestions();

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Research Suggestions</h2>
        <p className="text-gray-600 mb-6">
          Enter a biomedical research topic to generate AI-assisted brainstorming suggestions including gaps, future directions, and potential study ideas.
        </p>
        <ResearchSuggestionForm onSubmit={generateSuggestions} isLoading={isLoading} />
        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}
      </div>

      <ResearchSuggestionResults results={data} isLoading={isLoading} />
    </div>
  );
};
