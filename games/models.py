from django.db import models
from django.contrib.auth.models import User
import uuid

class GameRoom(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('playing', 'Playing'),
        ('finished', 'Finished'),
    ]
    
    code = models.CharField(max_length=8, unique=True, default='')
    name = models.CharField(max_length=100)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')
    players = models.ManyToManyField(User, related_name='game_rooms', blank=True)
    max_players = models.IntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    game_state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ChessGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('playing', 'Playing'),
        ('finished', 'Finished'),
    ]
    
    code = models.CharField(max_length=8, unique=True, default='')
    white_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chess_white', null=True, blank=True)
    black_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chess_black', null=True, blank=True)
    is_bot_game = models.BooleanField(default=False)
    bot_color = models.CharField(max_length=5, choices=[('white', 'White'), ('black', 'Black')], null=True, blank=True)
    current_turn = models.CharField(max_length=5, default='white')
    board_state = models.JSONField(default=dict)
    move_history = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    winner = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:8].upper()
        if not self.board_state:
            self.board_state = self.initialize_board()
        super().save(*args, **kwargs)
    
    def initialize_board(self):
        return {
            'a8': 'br', 'b8': 'bn', 'c8': 'bb', 'd8': 'bq', 'e8': 'bk', 'f8': 'bb', 'g8': 'bn', 'h8': 'br',
            'a7': 'bp', 'b7': 'bp', 'c7': 'bp', 'd7': 'bp', 'e7': 'bp', 'f7': 'bp', 'g7': 'bp', 'h7': 'bp',
            'a2': 'wp', 'b2': 'wp', 'c2': 'wp', 'd2': 'wp', 'e2': 'wp', 'f2': 'wp', 'g2': 'wp', 'h2': 'wp',
            'a1': 'wr', 'b1': 'wn', 'c1': 'wb', 'd1': 'wq', 'e1': 'wk', 'f1': 'wb', 'g1': 'wn', 'h1': 'wr',
        }
    
    def __str__(self):
        return f"Chess {self.code} - {self.status}"

class ChatMessage(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

class PlayerStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} Stats"
