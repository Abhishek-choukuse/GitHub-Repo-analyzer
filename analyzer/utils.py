import requests
from django.utils.dateparse import parse_datetime
from .models import GitHubRepo

import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_github_insight_openai(repo_data):
    """
    repo_data: dict containing repo details, e.g. name, description, stars, forks, etc.
    Returns AI-generated insight string.
    """

    prompt = (
        f"Analyze this GitHub repository information and provide a concise, insightful summary:\n\n"
        f"Name: {repo_data.get('name')}\n"
        f"Description: {repo_data.get('description')}\n"
        f"Stars: {repo_data.get('stars')}\n"
        f"Forks: {repo_data.get('forks')}\n"
        f"Open Issues: {repo_data.get('open_issues')}\n"
        f"Created At: {repo_data.get('created_at')}\n"
        f"Last Updated: {repo_data.get('last_updated')}\n\n"
        "Provide a brief summary (4-5 lines) highlighting the popularity, activity, major contributors."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes GitHub repos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        insight = response.choices[0].message.content.strip()
        return insight

    except Exception as e:
        return f"Error generating AI insight: {str(e)}"


def fetch_and_store_repo_data(repo_url):
    try:
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
    except IndexError:
        return None, "Invalid GitHub repo URL"

    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    response = requests.get(api_url)

    if response.status_code != 200:
        return None, f"GitHub API error: {response.status_code}"

    data = response.json()
    created_at = parse_datetime(data.get('created_at'))
    updated_at = parse_datetime(data.get('updated_at'))

    repo_data = {
    'name': data.get('name'),
    'stars': data.get('stargazers_count') or 0,
    'forks': data.get('forks_count') or 0,
    'open_issues': data.get('open_issues_count') or 0,
    'description': data.get('description') or '',
    'owner': owner,
    'created_at': created_at,
    'last_updated': updated_at,
}

    insight = generate_repo_insight(repo_data)

    repo_obj, created = GitHubRepo.objects.update_or_create(
        repo_url=repo_url,
        defaults={
            'name': data.get('name'),
            'owner': owner,
            'description': data.get('description') or '',
            'stars': data.get('stargazers_count') or 0,
            'forks': data.get('forks_count') or 0,
            'open_issues': data.get('open_issues_count') or 0,
            'created_at': created_at,
            'last_updated': updated_at,
            'repository_AI_insight': insight,
        }
    )

    return repo_obj, None
