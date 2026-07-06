import os
from pathlib import Path
from typing import Dict

class PromptRegistry:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load_prompt(self, template_name: str, variables: Dict[str, str]) -> str:
        prompt_path = self.base_dir / f"{template_name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template {template_name}.md not found at {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        for key, value in variables.items():
            # Basic escaping to prevent simple injection breaking the prompt
            safe_value = str(value).replace("{{", "{ {").replace("}}", "} }")
            template = template.replace(f"{{{{{key}}}}}", safe_value)

        return template

# Initialize the global registry instance
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "resources" / "prompts"
prompt_registry = PromptRegistry(PROMPTS_DIR)
