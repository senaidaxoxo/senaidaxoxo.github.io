import anthropic
import json
import os
import re
from datetime import datetime, timezone

def read_wiki(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return '(not found)'

def generate():
    today    = datetime.now(timezone.utc).strftime('%A, %B %d, %Y')
    date_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    now_iso  = datetime.now(timezone.utc).isoformat(timespec='seconds')

    wiki = {k: read_wiki(f'wiki/self/{v}') for k, v in {
        'goals':    'Goals.md',
        'values':   'Values.md',
        'work':     'Work.md',
        'patterns': 'Patterns.md',
        'health':   'Health.md',
        'identity': 'Identity.md',
    }.items()}

    prompt = f"""You are generating a personal morning briefing for Senaida.

Today is {today}.

== PERSONAL WIKI ==

GOALS:
{wiki['goals']}

VALUES:
{wiki['values']}

CURRENT WORK:
{wiki['work']}

PATTERNS:
{wiki['patterns']}

HEALTH:
{wiki['health']}

IDENTITY:
{wiki['identity']}

== TASK ==

Write a warm, specific morning briefing. Reference her actual goals and work — not generic advice.
Be concise. One insight per section.

Respond with ONLY valid JSON — no markdown fences, no explanation:
{{
  "date": "{date_iso}",
  "generated_at": "{now_iso}",
  "greeting": "one warm sentence greeting her by first name",
  "focus": ["specific focus item 1", "specific focus item 2", "specific focus item 3"],
  "reminder": "one or two sentences about a pattern, health habit, or intention worth holding today",
  "thought": "one short sentence — an insight or encouragement rooted in her values"
}}"""

    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    msg = client.messages.create(
        model='claude-sonnet-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )

    text = msg.content[0].text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text.strip())

    briefing = json.loads(text)

    with open('briefing.json', 'w', encoding='utf-8') as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)

    print(f"Generated briefing for {date_iso}")

if __name__ == '__main__':
    generate()
