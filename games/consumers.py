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



class ChessConsumer(AsyncWebsocketConsumer):
    waiting_players = []
    
    async def connect(self):
        self.game_code = self.scope['url_route']['kwargs'].get('game_code')
        self.user = self.scope['user']
        
        if self.game_code:
            # Join existing game
            self.room_group_name = f'chess_{self.game_code}'
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            await self.send_game_state()
        else:
            # Matchmaking
            await self.accept()
            await self.handle_matchmaking()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        
        if msg_type == 'move':
            await self.handle_move(data)
        elif msg_type == 'resign':
            await self.handle_resign()
    
    async def handle_matchmaking(self):
        ChessConsumer.waiting_players.append({
            'channel': self.channel_name,
            'user': self.user.username,
            'user_id': self.user.id
        })
        
        # Only match if we have 2 or more players
        if len(ChessConsumer.waiting_players) >= 2:
            # Match two players
            p1 = ChessConsumer.waiting_players.pop(0)
            p2 = ChessConsumer.waiting_players.pop(0)
            game = await self.create_game(p1['user_id'], p2['user_id'], False)
            
            for player in [p1, p2]:
                await self.channel_layer.send(player['channel'], {
                    'type': 'match_found',
                    'game_code': game.code
                })
        # If still waiting, send waiting status
        else:
            await self.send(text_data=json.dumps({
                'type': 'waiting',
                'message': 'Searching for opponent...'
            }))
    
    async def match_found(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'game_code': event['game_code'],
            'is_bot': event.get('is_bot', False)
        }))
    
    async def handle_move(self, data):
        from_pos = data['from']
        to_pos = data['to']
        
        game = await self.get_game()
        if not game:
            return
        
        # Validate turn
        player_color = await self.get_player_color(game)
        if game.current_turn != player_color:
            return
        
        # Make move
        if from_pos in game.board_state:
            piece = game.board_state[from_pos]
            game.board_state[to_pos] = piece
            del game.board_state[from_pos]
            game.current_turn = 'black' if game.current_turn == 'white' else 'white'
            game.move_history.append({'from': from_pos, 'to': to_pos, 'piece': piece})
            await self.save_game(game)
            
            # Broadcast move
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_update',
                'board_state': game.board_state,
                'current_turn': game.current_turn,
                'move': {'from': from_pos, 'to': to_pos}
            })
            
            # Bot move if needed
            if game.is_bot_game and game.current_turn == game.bot_color:
                await self.make_bot_move(game)
    
    async def make_bot_move(self, game):
        from .chess_bot import ChessBot
        import asyncio
        
        await asyncio.sleep(1)  # Delay for realism
        
        move = ChessBot.make_move(game.board_state, game.bot_color)
        if move:
            from_pos, to_pos = move
            piece = game.board_state[from_pos]
            game.board_state[to_pos] = piece
            del game.board_state[from_pos]
            game.current_turn = 'white' if game.current_turn == 'black' else 'black'
            game.move_history.append({'from': from_pos, 'to': to_pos, 'piece': piece, 'bot': True})
            await self.save_game(game)
            
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_update',
                'board_state': game.board_state,
                'current_turn': game.current_turn,
                'move': {'from': from_pos, 'to': to_pos, 'bot': True}
            })
    
    async def handle_resign(self):
        game = await self.get_game()
        if game:
            player_color = await self.get_player_color(game)
            winner = 'black' if player_color == 'white' else 'white'
            game.status = 'finished'
            game.winner = winner
            await self.save_game(game)
            
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_over',
                'winner': winner,
                'reason': 'resignation'
            })
    
    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'board_state': event['board_state'],
            'current_turn': event['current_turn'],
            'move': event['move']
        }))
    
    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'winner': event['winner'],
            'reason': event['reason']
        }))
    
    async def send_game_state(self):
        game = await self.get_game()
        if game:
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'board_state': game.board_state,
                'current_turn': game.current_turn,
                'is_bot_game': game.is_bot_game,
                'bot_color': game.bot_color
            }))
    
    @database_sync_to_async
    def get_game(self):
        try:
            return ChessGame.objects.get(code=self.game_code)
        except ChessGame.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_game(self, game):
        game.save()
    
    @database_sync_to_async
    def get_player_color(self, game):
        if game.white_player_id == self.user.id:
            return 'white'
        elif game.black_player_id == self.user.id:
            return 'black'
        return None
    
    @database_sync_to_async
    def create_game(self, white_id, black_id, is_bot):
        from django.contrib.auth.models import User
        import random
        
        white_player = User.objects.get(id=white_id)
        black_player = User.objects.get(id=black_id) if black_id else None
        
        game = ChessGame.objects.create(
            white_player=white_player,
            black_player=black_player,
            is_bot_game=is_bot,
            bot_color='black' if is_bot else None,
            status='playing'
        )
        return game
