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
