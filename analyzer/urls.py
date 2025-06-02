from django.urls import path
from . import views

urlpatterns = [
    path('', views.repo_input_view, name='repo_input'),
    path('repo/<int:repo_id>/', views.repo_detail_view, name='repo_detail'),
]
