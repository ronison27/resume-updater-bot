"""
🧹 Text Cleaner
Removes AI intro/outro text from the response
Keeps only the actual resume content
"""

import re


def clean_ai_response(text):
    """Remove AI intro/outro text and keep only resume content"""

    # List of AI intro phrases to remove
    intro_phrases = [
        r"(?i)^here is the updated resume[:\s]*",
        r"(?i)^here is your updated resume[:\s]*",
        r"(?i)^here's the updated resume[:\s]*",
        r"(?i)^here's your updated resume[:\s]*",
        r"(?i)^here is the rewritten resume[:\s]*",
        r"(?i)^here is your rewritten resume[:\s]*",
        r"(?i)^below is the updated resume[:\s]*",
        r"(?i)^below is your updated resume[:\s]*",
        r"(?i)^below is the rewritten resume[:\s]*",
        r"(?i)^sure[!.,]?\s*here is[^:]*[:\s]*",
        r"(?i)^sure[!.,]?\s*here's[^:]*[:\s]*",
        r"(?i)^sure[!.,]?\s*below[^:]*[:\s]*",
        r"(?i)^certainly[!.,]?\s*here[^:]*[:\s]*",
        r"(?i)^absolutely[!.,]?\s*here[^:]*[:\s]*",
        r"(?i)^of course[!.,]?\s*here[^:]*[:\s]*",
        r"(?i)^i've updated[^:]*[:\s]*",
        r"(?i)^i have updated[^:]*[:\s]*",
        r"(?i)^i've rewritten[^:]*[:\s]*",
        r"(?i)^i have rewritten[^:]*[:\s]*",
        r"(?i)^the updated resume[:\s]*",
        r"(?i)^updated resume[:\s]*",
        r"(?i)^please find[^:]*[:\s]*",
        r"(?i)^find below[^:]*[:\s]*",
    ]

    # List of AI outro phrases to remove
    outro_phrases = [
        r"(?i)let me know if you.*$",
        r"(?i)feel free to.*$",
        r"(?i)hope this helps.*$",
        r"(?i)i hope this.*$",
        r"(?i)if you need any.*$",
        r"(?i)if you have any.*$",
        r"(?i)is there anything.*$",
        r"(?i)do you want me to.*$",
        r"(?i)would you like me to.*$",
        r"(?i)shall i.*$",
        r"(?i)note:.*$",
        r"(?i)please note:.*$",
        r"(?i)key changes made:.*$",
        r"(?i)changes made:.*$",
        r"(?i)key changes:.*$",
        r"(?i)modifications:.*$",
        r"(?i)what i changed:.*$",
        r"(?i)summary of changes:.*$",
    ]

    # Remove intro phrases
    lines = text.strip().split('\n')
    cleaned_lines = []
    content_started = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines at the beginning
        if not content_started and not stripped:
            continue

        # Check if this is an intro line
        is_intro = False
        if not content_started:
            for pattern in intro_phrases:
                if re.match(pattern, stripped):
                    is_intro = True
                    break

        if is_intro:
            continue

        # Content has started
        content_started = True
        cleaned_lines.append(line)

    # Remove outro phrases from the end
    while cleaned_lines:
        last_line = cleaned_lines[-1].strip()

        if not last_line:
            cleaned_lines.pop()
            continue

        is_outro = False
        for pattern in outro_phrases:
            if re.match(pattern, last_line):
                is_outro = True
                break

        if is_outro:
            cleaned_lines.pop()
        else:
            break

    # Remove markdown code block markers
    result = '\n'.join(cleaned_lines)
    result = result.strip('`')
    result = re.sub(r'^```\w*\n?', '', result)
    result = re.sub(r'\n?```$', '', result)

    # Remove "---" separator lines at the very end
    result = result.rstrip('-').rstrip()

    return result.strip()