from django.urls import path
from . import views
urlpatterns = [
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('profile/', views.profile_view, name='accounts.profile_me'),
    path('profile/edit/', views.profile_edit, name='accounts.profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='accounts.profile_user'),
    path('settings/', views.settings_view, name='accounts.settings'),
    path('search/', views.search_profiles, name='accounts.search'),
    path('connections/', views.connections_list, name='accounts.connections'),
    path('connect/<str:username>/', views.send_connection_request, name='accounts.connect'),
    path('connection/accept/<int:connection_id>/', views.accept_connection, name='accounts.accept_connection'),
    path('connection/decline/<int:connection_id>/', views.decline_connection, name='accounts.decline_connection'),
    path('connection/remove/<str:username>/', views.remove_connection, name='accounts.remove_connection'),
    path('candidates/', views.candidate_search, name='candidate_search'),
]