from django.db import models


class GitHubRepo(models.Model):
    repo_url = models.URLField(unique=True)
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stars = models.PositiveIntegerField(default=0)
    forks = models.PositiveIntegerField(default=0)
    open_issues = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField()
    last_updated = models.DateTimeField()
    data_fetched_at = models.DateTimeField(auto_now=True)
    repository_AI_insight = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.owner}/{self.name}"

