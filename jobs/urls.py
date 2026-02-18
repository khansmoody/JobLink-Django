from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('post/', views.job_post, name='job_post'),  # User Story #10
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),  # User Story #10
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('applications/', views.my_applications, name='my_applications'),
    path('kanban/', views.kanban, name = 'kanban')

]
