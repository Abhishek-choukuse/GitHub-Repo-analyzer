from django.db import models

class GitHubRepo(models.Model):
    repo_url = models.URLField(unique=True)
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    stars = models.PositiveIntegerField(default=0)
    forks = models.PositiveIntegerField(default=0)
    open_issues = models.PositiveIntegerField(default=0)
    watchers = models.PositiveIntegerField(default=0)
    subscribers = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField()
    last_updated = models.DateTimeField()
    data_fetched_at = models.DateTimeField(auto_now=True)

    languages = models.TextField(blank=True, null=True)       
    commit_timeline = models.TextField(blank=True, null=True) 
    top_contributors = models.TextField(blank=True, null=True)

    pull_requests = models.TextField(blank=True, null=True)   
    releases = models.TextField(blank=True, null=True)      
    issue_aging = models.TextField(blank=True, null=True)    

    repo_insight = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.owner}/{self.name}"
