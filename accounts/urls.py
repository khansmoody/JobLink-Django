from django.urls import path
from . import views
urlpatterns = [
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('profile/', views.profile_view, name='accounts.profile_me'),
    path('profile/edit/', views.profile_edit, name='accounts.profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='accounts.profile_user'),
]