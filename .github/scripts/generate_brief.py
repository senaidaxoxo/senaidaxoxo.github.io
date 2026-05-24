import anthropic
import base64
import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

def read_wiki(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return '(not found)'

def github_api(method, path, body=None):
    token = os.environ['GITHUB_TOKEN']
    repo  = os.environ['GITHUB_REPOSITORY']
    url   = f'https://api.github.com/repos/{repo}{path}'
    data  = json.dumps(body).encode() if body else None
    req   = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'token {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/vnd.github+json')
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

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

    # Push directly via GitHub API — no git commit/push race conditions
    content_str = json.dumps(briefing, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode()).decode()

    # Get current file SHA (needed for update)
    current = github_api('GET', '/contents/briefing.json')
    sha = current['sha']

    github_api('PUT', '/contents/briefing.json', {
        'message': f'chore: morning brief {date_iso}',
        'content': content_b64,
        'sha': sha,
    })

    print(f"Briefing for {date_iso} pushed via GitHub API")

if __name__ == '__main__':
    generate()
