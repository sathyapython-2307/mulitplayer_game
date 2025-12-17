from django.contrib import admin
from .models import GameRoom, ChatMessage, PlayerStats, ChessGame

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

@admin.register(ChessGame)
class ChessGameAdmin(admin.ModelAdmin):
    list_display = ['code', 'white_player', 'black_player', 'is_bot_game', 'status', 'created_at']
    list_filter = ['status', 'is_bot_game']
