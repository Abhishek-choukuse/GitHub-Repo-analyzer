from django.shortcuts import render, redirect, get_object_or_404
from .utils import fetch_and_store_repo_data  
from django.urls import reverse
from .models import GitHubRepo

def repo_detail_view(request, repo_id):
    repo = get_object_or_404(GitHubRepo, id=repo_id)
    return render(request, 'analyzer/repo_detail.html', {'repo': repo})


def repo_input_view(request):
    error = None

    if request.method == 'POST':
        repo_url = request.POST.get('repo_url')
        if repo_url:
            repo_obj, error = fetch_and_store_repo_data(repo_url)

            if repo_obj:
                # Redirect to the detail view for this repo
                return redirect(reverse('repo_detail', args=[repo_obj.id]))

    return render(request, 'analyzer/repo_input.html', {'error': error})
