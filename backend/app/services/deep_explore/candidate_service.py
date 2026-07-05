import json
import os
import re
from typing import List, Dict, Any

class CandidateExtractor:
    def __init__(self):
        self.rules = self._load_rules()
        self.min_length_threshold = 30 # characters

    def _load_rules(self) -> Dict[str, List[str]]:
        base_dir = os.path.dirname(__file__)
        rules_path = os.path.join(base_dir, '..', '..', 'resources', 'candidate_rules', 'rules.json')
        with open(rules_path, 'r') as f:
            return json.load(f)

    def _split_into_sentences(self, text: str) -> List[str]:
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_candidates(self, paper: Dict) -> List[Dict[str, Any]]:
        """
        Takes a processed paper dictionary with sections.
        Returns a list of candidate objects.
        """
        candidates = []
        pmid = paper["pmid"]
        pmcid = paper["pmcid"]
        sections = paper.get("sections", {})

        paragraph_id_counter = 1

        for section_name, paragraphs in sections.items():
            for paragraph in paragraphs:
                sentences = self._split_into_sentences(paragraph)

                matched_categories = set()
                matched_sentence_indices = []

                # Evaluate each sentence
                for i, sentence in enumerate(sentences):
                    sentence_lower = sentence.lower()
                    sentence_matched = False

                    for category, phrases in self.rules.items():
                        for phrase in phrases:
                            if phrase in sentence_lower:
                                matched_categories.add(category)
                                sentence_matched = True
                                break # No need to check other phrases in this category for this sentence

                    if sentence_matched:
                        matched_sentence_indices.append(i)

                if matched_categories:
                    # Context expansion
                    expanded_text = self._expand_context(sentences, matched_sentence_indices)

                    if len(expanded_text) >= self.min_length_threshold:
                        candidates.append({
                            "pmid": pmid,
                            "pmcid": pmcid,
                            "section": section_name,
                            "paragraph_id": paragraph_id_counter,
                            "text": expanded_text,
                            "matched_rule_categories": list(matched_categories)
                        })

                paragraph_id_counter += 1

        return candidates

    def _expand_context(self, sentences: List[str], matched_indices: List[int]) -> str:
        """
        Includes previous and following sentences for context.
        """
        indices_to_include = set()
        for idx in matched_indices:
            indices_to_include.add(idx)
            if idx > 0:
                indices_to_include.add(idx - 1)
            if idx < len(sentences) - 1:
                indices_to_include.add(idx + 1)

        sorted_indices = sorted(list(indices_to_include))

        # Join the selected sentences
        expanded_sentences = [sentences[i] for i in sorted_indices]
        return " ".join(expanded_sentences)

candidate_extractor = CandidateExtractor()
