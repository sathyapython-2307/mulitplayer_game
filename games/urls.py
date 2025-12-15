from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('lobby/', views.lobby, name='lobby'),
    path('matchmaking/', views.matchmaking, name='matchmaking'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/<str:code>/', views.join_room, name='join_room'),
    path('room/<str:code>/', views.game_room, name='game_room'),
    path('leave-room/<str:code>/', views.leave_room, name='leave_room'),
]
