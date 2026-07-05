import json

def parse(text_content):
    try:
        # First attempt: direct json.loads
        return json.loads(text_content)
    except json.JSONDecodeError:
        # Second attempt: maybe it's wrapped in markdown
        import re
        match = re.search(r'```json\s*(.*?)\s*```', text_content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError("Failed to parse JSON")

print(parse('{"test": 123}'))
print(parse('```json\n{"test": 123}\n```'))
