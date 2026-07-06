import React, { useState } from 'react';

interface Props {
  title: string;
  items: string[];
}

export const SectionCard: React.FC<Props> = ({ title, items }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!items || items.length === 0) return null;

  const handleCopy = () => {
    const textToCopy = `${title}\n${items.map(item => `- ${item}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4 overflow-hidden">
      <div
        className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="text-lg font-medium text-gray-800 flex items-center">
          <span className="mr-2">{isExpanded ? '▼' : '▶'}</span>
          {title} <span className="ml-2 text-sm font-normal text-gray-500">({items.length})</span>
        </h3>
        <button
          onClick={(e) => { e.stopPropagation(); handleCopy(); }}
          className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none"
          title="Copy to clipboard"
        >
          Copy
        </button>
      </div>

      {isExpanded && (
        <div className="p-4">
          <ul className="list-disc pl-5 space-y-2 text-gray-700">
            {items.map((item, index) => (
              <li key={index} className="pl-1 leading-relaxed">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
