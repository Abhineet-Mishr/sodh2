import os

def load_prompt(prompt_path: str, **kwargs) -> str:
    """
    Loads a prompt file and injects variables.
    `prompt_path` should be relative to `backend/app/resources/prompts/`
    """
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'prompts')
    full_path = os.path.join(base_dir, prompt_path)

    with open(full_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    for key, value in kwargs.items():
        placeholder = f"{{{{{key}}}}}"
        prompt_content = prompt_content.replace(placeholder, str(value) if value else "")

    return prompt_content
