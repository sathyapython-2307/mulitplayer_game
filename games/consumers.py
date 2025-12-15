import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameRoom, ChatMessage

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'
        self.user = self.scope['user']
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.broadcast_players()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.broadcast_players()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        
        if msg_type == 'chat':
            await self.save_message(data['message'])
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message': data['message'],
                'username': self.user.username
            })
        elif msg_type == 'game_action':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_update',
                'action': data['action'],
                'data': data.get('data', {}),
                'username': self.user.username
            })
        elif msg_type == 'start_game':
            await self.update_room_status('playing')
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_started',
                'username': self.user.username
            })
        elif msg_type == 'game_state':
            await self.save_game_state(data['state'])
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'state_sync',
                'state': data['state']
            })
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'username': event['username']
        }))
    
    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_action',
            'action': event['action'],
            'data': event['data'],
            'username': event['username']
        }))
    
    async def game_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'username': event['username']
        }))
    
    async def state_sync(self, event):
        await self.send(text_data=json.dumps({
            'type': 'state_sync',
            'state': event['state']
        }))
    
    async def player_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_update',
            'players': event['players']
        }))
    
    async def broadcast_players(self):
        players = await self.get_players()
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'player_update',
            'players': players
        })
    
    @database_sync_to_async
    def get_players(self):
        try:
            room = GameRoom.objects.get(code=self.room_code)
            return list(room.players.values_list('username', flat=True))
        except GameRoom.DoesNotExist:
            return []
    
    @database_sync_to_async
    def save_message(self, content):
        room = GameRoom.objects.get(code=self.room_code)
        ChatMessage.objects.create(room=room, user=self.user, content=content)
    
    @database_sync_to_async
    def update_room_status(self, status):
        room = GameRoom.objects.get(code=self.room_code)
        room.status = status
        room.save()
    
    @database_sync_to_async
    def save_game_state(self, state):
        room = GameRoom.objects.get(code=self.room_code)
        room.game_state = state
        room.save()


class MatchmakingConsumer(AsyncWebsocketConsumer):
    waiting_players = []
    
    async def connect(self):
        self.user = self.scope['user']
        await self.channel_layer.group_add('matchmaking', self.channel_name)
        await self.accept()
        MatchmakingConsumer.waiting_players.append({
            'channel': self.channel_name,
            'user': self.user.username
        })
        await self.try_match()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('matchmaking', self.channel_name)
        MatchmakingConsumer.waiting_players = [
            p for p in MatchmakingConsumer.waiting_players 
            if p['channel'] != self.channel_name
        ]
    
    async def try_match(self):
        if len(MatchmakingConsumer.waiting_players) >= 2:
            p1 = MatchmakingConsumer.waiting_players.pop(0)
            p2 = MatchmakingConsumer.waiting_players.pop(0)
            room = await self.create_match_room(p1['user'], p2['user'])
            for player in [p1, p2]:
                await self.channel_layer.send(player['channel'], {
                    'type': 'match_found',
                    'room_code': room.code
                })
    
    async def match_found(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'room_code': event['room_code']
        }))
    
    @database_sync_to_async
    def create_match_room(self, user1, user2):
        from django.contrib.auth.models import User
        host = User.objects.get(username=user1)
        player2 = User.objects.get(username=user2)
        room = GameRoom.objects.create(host=host, name=f"Match: {user1} vs {user2}", max_players=2)
        room.players.add(host, player2)
        return room
