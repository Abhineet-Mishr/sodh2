import { useState } from 'react';
import { ResearchSuggestionRequest, ResearchSuggestionResponse } from './types';
import { fetchResearchSuggestions } from '../../../lib/literature_api';

export const useResearchSuggestions = () => {
  const [data, setData] = useState<ResearchSuggestionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateSuggestions = async (request: ResearchSuggestionRequest) => {
    setIsLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetchResearchSuggestions(request);
      setData(response);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred while fetching suggestions.');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    data,
    isLoading,
    error,
    generateSuggestions,
  };
};
