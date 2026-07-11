import { ResearchSuggestionRequest, ResearchSuggestionResponse } from './types';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const API_PREFIX = `${API_BASE}/api/literature`;

export const fetchResearchSuggestions = async (request: ResearchSuggestionRequest): Promise<ResearchSuggestionResponse> => {
  const response = await fetch(`${API_PREFIX}/research-suggestions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
};
