from django.shortcuts import render, redirect, get_object_or_404
from .utils import fetch_and_store_repo_data  
from django.urls import reverse
from .models import GitHubRepo
import json

def repo_detail_view(request, repo_id):
    repo = get_object_or_404(GitHubRepo, id=repo_id)

    context = {
        'repo': repo,
        'languages': json.loads(repo.languages or '{}'),
        'top_contributors': json.loads(repo.top_contributors or '[]'),
        'commit_timeline': json.loads(repo.commit_timeline or '[]'),
        'pull_requests': json.loads(repo.pull_requests or '{}'),
        'releases': json.loads(repo.releases or '[]'),
        'issue_aging': json.loads(repo.issue_aging or '{}'),
    }
    
    return render(request, 'analyzer/repo_detail.html', context)


def repo_input_view(request):
    error = None

    if request.method == 'POST':
        repo_url = request.POST.get('repo_url')
        if repo_url:
            repo_obj, error = fetch_and_store_repo_data(repo_url)

            if repo_obj:
                return redirect(reverse('repo_detail', args=[repo_obj.id]))

    return render(request, 'analyzer/repo_input.html', {'error': error})
