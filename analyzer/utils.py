import requests
import os
import json
from datetime import datetime, timezone
from django.utils.dateparse import parse_datetime
from .models import GitHubRepo
from openai import OpenAI, OpenAIError
from dashscope import Generation

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_insight_rule_based(repo_data):
    name = repo_data.get('name', 'Unknown')
    description = repo_data.get('description', 'No description provided.')
    stars = repo_data.get('stars', 0)
    forks = repo_data.get('forks', 0)
    issues = repo_data.get('open_issues', 0)
    watchers = repo_data.get('watchers', 0)
    subscribers = repo_data.get('subscribers', 0)
    created_at = repo_data.get('created_at')
    updated_at = repo_data.get('last_updated')

    created_str = created_at.strftime("%b %d, %Y") if created_at else "Unknown"
    updated_str = updated_at.strftime("%b %d, %Y") if updated_at else "Unknown"

    if stars > 500:
        popularity = "highly popular"
    elif stars > 100:
        popularity = "moderately popular"
    else:
        popularity = "relatively new or less known"

    if updated_at and (datetime.now(timezone.utc) - updated_at).days < 30:
        activity = "actively maintained"
    else:
        activity = "less active recently"

    if created_at:
        age_days = (datetime.now(timezone.utc) - created_at).days
        if age_days > 1000:
            timeline = "mature and well-established"
        elif age_days > 300:
            timeline = "moderately aged"
        else:
            timeline = "fairly new"
    else:
        timeline = "of unknown age"

    insight = (
        f"'{name}' is a {popularity} GitHub repository with {stars} stars, {watchers} watchers, "
        f"and {subscribers} subscribers. It is {activity}, has {forks} forks, and {issues} open issues. "
        f"The project was created on {created_str} and last updated on {updated_str}, "
        f"indicating it is {timeline}. "
        f"Description: {description}. "
        f"Additional data such as commit history, pull requests, releases, languages, and issue aging provide further insight."
    )

    return insight


def generate_repo_insight_from_ai(repo_data):
    prompt = (
        f"Analyze this GitHub repository information and provide a concise, insightful summary:\n\n"
        f"Name: {repo_data.get('name')}\n"
        f"Description: {repo_data.get('description')}\n"
        f"Stars: {repo_data.get('stars')}\n"
        f"Forks: {repo_data.get('forks')}\n"
        f"Open Issues: {repo_data.get('open_issues')}\n"
        f"Watchers: {repo_data.get('watchers')}\n"
        f"Subscribers: {repo_data.get('subscribers')}\n"
        f"Created At: {repo_data.get('created_at')}\n"
        f"Last Updated: {repo_data.get('last_updated')}\n"
        f"Languages: {repo_data.get('languages')}\n"
        f"Commit Timeline: {repo_data.get('commit_timeline')}\n"
        f"Top Contributors: {repo_data.get('top_contributors')}\n"
        f"Pull Requests: {repo_data.get('pull_requests')}\n"
        f"Releases: {repo_data.get('releases')}\n"
        f"Issue Aging: {repo_data.get('issue_aging')}\n\n"
        "Provide a detailed overview highlighting the popularity, recent activity, major contributors, timeline etc."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes GitHub repos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        print(f"OpenAI API failed, falling back to Qwen Chat: {e}")

        try:
            response = Generation.call(
                model="qwen:chat",
                prompt=prompt,
                top_p=0.8,
                temperature=0.7,
                api_key=os.getenv("DASHSCOPE_API_KEY")
            )
            return response['output']['text']

        except Exception as qe:
            print(f"Qwen Chat failed, falling back to rule-based: {qe}")
            return generate_insight_rule_based(repo_data)


def generate_repo_insight(repo_data):
    return generate_repo_insight_from_ai(repo_data)


def fetch_and_store_repo_data(repo_url):
    try:
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
    except IndexError:
        return None, "Invalid GitHub repo URL"

    headers = {'Accept': 'application/vnd.github.v3+json'}

    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    repo_resp = requests.get(api_url, headers=headers)
    if repo_resp.status_code != 200:
        return None, f"GitHub API error: {repo_resp.status_code}"
    repo_json = repo_resp.json()

    languages_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/languages', headers=headers)
    languages_json = languages_resp.json() if languages_resp.status_code == 200 else {}

    contributors_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/contributors', headers=headers)
    contributors_json = contributors_resp.json() if contributors_resp.status_code == 200 else []

    pulls_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1', headers=headers)
    pull_count = 0
    if pulls_resp.status_code == 200:
        if 'Link' in pulls_resp.headers:
            links = pulls_resp.headers['Link']
            import re
            match = re.search(r'&page=(\d+)>; rel="last"', links)
            if match:
                pull_count = int(match.group(1))
            else:
                pull_count = len(pulls_resp.json())
        else:
            pull_count = len(pulls_resp.json())


    releases_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/releases', headers=headers)
    releases_json = releases_resp.json() if releases_resp.status_code == 200 else []

    watchers = repo_json.get('watchers_count', 0)
    subscribers = repo_json.get('subscribers_count', 0)

    issues_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=100', headers=headers)
    issue_aging = {"less_than_7_days": 0, "between_7_and_30_days": 0, "more_than_30_days": 0}
    if issues_resp.status_code == 200:
        issues = issues_resp.json()
        now = datetime.utcnow()
        for issue in issues:
            if 'pull_request' in issue:
                continue  
            created = parse_datetime(issue.get('created_at'))
            if not created:
                continue
            delta = (now - created).days
            if delta < 7:
                issue_aging["less_than_7_days"] += 1
            elif delta <= 30:
                issue_aging["between_7_and_30_days"] += 1
            else:
                issue_aging["more_than_30_days"] += 1


    commits_resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}/stats/commit_activity', headers=headers)
    commit_timeline = commits_resp.json() if commits_resp.status_code == 200 else []

    created_at = parse_datetime(repo_json.get('created_at'))
    updated_at = parse_datetime(repo_json.get('updated_at'))


    top_contributors = []
    for c in contributors_json:
        top_contributors.append({"login": c.get("login"), "contributions": c.get("contributions")})

    repo_data = {
        'name': repo_json.get('name'),
        'stars': repo_json.get('stargazers_count', 0),
        'forks': repo_json.get('forks_count', 0),
        'open_issues': repo_json.get('open_issues_count', 0),
        'description': repo_json.get('description') or '',
        'owner': owner,
        'created_at': created_at,
        'last_updated': updated_at,
        'watchers': watchers,
        'subscribers': subscribers,
        'languages': json.dumps(languages_json),
        'commit_timeline': json.dumps(commit_timeline),
        'top_contributors': json.dumps(top_contributors),
        'pull_requests': json.dumps({"count": pull_count}),
        'releases': json.dumps(releases_json),
        'issue_aging': json.dumps(issue_aging),
    }

    insight = generate_repo_insight(repo_data)

    repo_obj, created = GitHubRepo.objects.update_or_create(
        repo_url=repo_url,
        defaults={
            'name': repo_json.get('name'),
            'owner': owner,
            'description': repo_json.get('description') or '',
            'stars': repo_json.get('stargazers_count', 0),
            'forks': repo_json.get('forks_count', 0),
            'open_issues': repo_json.get('open_issues_count', 0),
            'created_at': created_at,
            'last_updated': updated_at,
            'watchers': watchers,
            'subscribers': subscribers,
            'languages': json.dumps(languages_json),
            'commit_timeline': json.dumps(commit_timeline),
            'top_contributors': json.dumps(top_contributors),
            'pull_requests': json.dumps({"count": pull_count}),
            'releases': json.dumps(releases_json),
            'issue_aging': json.dumps(issue_aging),
            'repo_insight': insight,
        }
    )

    return repo_obj, None
