from django.contrib import admin
from .models import GitHubRepo

@admin.register(GitHubRepo)
class GitHubRepoAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'stars', 'forks', 'open_issues', 'created_at', 'last_updated')
    search_fields = ('owner', 'name')
