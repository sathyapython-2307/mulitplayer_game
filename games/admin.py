from django.contrib import admin
from .models import GameRoom, ChatMessage, PlayerStats

@admin.register(GameRoom)
class GameRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'host', 'status', 'created_at']
    list_filter = ['status']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'timestamp']

@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'games_played', 'games_won', 'score']
