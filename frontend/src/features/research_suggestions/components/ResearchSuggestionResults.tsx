import React from 'react';
import { ResearchSuggestionResponse } from './types';
import { SectionCard } from './SectionCard';

interface Props {
  response: ResearchSuggestionResponse;
}

export const ResearchSuggestionResults: React.FC<Props> = ({ response }) => {
  const { data, model, processing_time, credits_used, topic } = response;

  return (
    <div className="mt-8 animate-fade-in">
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-r-lg">
        <h3 className="text-lg font-medium text-blue-800 mb-2">Results for: "{topic}"</h3>
        <p className="text-sm text-blue-600 mb-2">{data.summary}</p>
        <div className="flex gap-4 text-xs text-blue-500 mt-3 font-medium">
          <span>Model: {model}</span>
          <span>Time: {processing_time}s</span>
          <span>Credits Used: {credits_used}</span>
        </div>
      </div>

      <div className="space-y-4">
        <SectionCard title="Emerging Topics" items={data.emerging_topics} />
        <SectionCard title="Identified Research Gaps" items={data.research_gaps} />
        <SectionCard title="Future Directions" items={data.future_directions} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <SectionCard title="Clinical Studies" items={data.clinical_studies} />
            <SectionCard title="Cohort Studies" items={data.cohort_studies} />
          </div>
          <div>
            <SectionCard title="RCT Ideas" items={data.rct_ideas} />
            <SectionCard title="SRMA Topics" items={data.srma_topics} />
          </div>
        </div>

        <SectionCard title="Interdisciplinary Ideas" items={data.interdisciplinary_ideas} />
        <SectionCard title="AI / ML Opportunities" items={data.ai_ml_opportunities} />

        {data.references && data.references.length > 0 && (
          <SectionCard title="Relevant References" items={data.references} />
        )}
      </div>
    </div>
  );
};
