import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameRoom, ChatMessage, ChessGame


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


# Chess Matchmaking Consumer - handles player vs player matching
class ChessMatchmakingConsumer(AsyncWebsocketConsumer):
    waiting_players = []
    
    async def connect(self):
        self.user = self.scope['user']
        await self.accept()
        
        # Remove any existing entry for this user
        ChessMatchmakingConsumer.waiting_players = [
            p for p in ChessMatchmakingConsumer.waiting_players 
            if p['user_id'] != self.user.id
        ]
        
        # Add to waiting list
        ChessMatchmakingConsumer.waiting_players.append({
            'channel': self.channel_name,
            'user': self.user.username,
            'user_id': self.user.id
        })
        
        # Try to match
        await self.try_match()
    
    async def disconnect(self, close_code):
        # Remove from waiting list
        ChessMatchmakingConsumer.waiting_players = [
            p for p in ChessMatchmakingConsumer.waiting_players 
            if p['channel'] != self.channel_name
        ]
    
    async def try_match(self):
        # Need at least 2 players to match
        if len(ChessMatchmakingConsumer.waiting_players) >= 2:
            p1 = ChessMatchmakingConsumer.waiting_players.pop(0)
            p2 = ChessMatchmakingConsumer.waiting_players.pop(0)
            
            # Create game
            game = await self.create_chess_game(p1['user_id'], p2['user_id'])
            
            # Notify both players
            for player in [p1, p2]:
                await self.channel_layer.send(player['channel'], {
                    'type': 'match_found',
                    'game_code': game.code
                })
        else:
            # Send waiting status
            await self.send(text_data=json.dumps({
                'type': 'waiting',
                'message': 'Searching for opponent...',
                'queue_position': len(ChessMatchmakingConsumer.waiting_players)
            }))
    
    async def match_found(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'game_code': event['game_code']
        }))
    
    @database_sync_to_async
    def create_chess_game(self, white_id, black_id):
        from django.contrib.auth.models import User
        white_player = User.objects.get(id=white_id)
        black_player = User.objects.get(id=black_id)
        
        game = ChessGame.objects.create(
            white_player=white_player,
            black_player=black_player,
            is_bot_game=False,
            status='playing'
        )
        return game


# Chess Game Consumer - handles actual gameplay
class ChessGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_code = self.scope['url_route']['kwargs']['game_code']
        self.room_group_name = f'chess_{self.game_code}'
        self.user = self.scope['user']
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send current game state
        await self.send_game_state()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        
        if msg_type == 'move':
            await self.handle_move(data)
        elif msg_type == 'resign':
            await self.handle_resign()
        elif msg_type == 'get_state':
            await self.send_game_state()
    
    async def handle_move(self, data):
        from_pos = data['from']
        to_pos = data['to']
        promotion = data.get('promotion')  # 'q', 'r', 'b', 'n' for pawn promotion
        
        game = await self.get_game()
        if not game:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Game not found'}))
            return
        
        # Validate turn
        player_color = await self.get_player_color(game)
        if not player_color:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Not a player in this game'}))
            return
            
        if game.current_turn != player_color:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Not your turn'}))
            return
        
        # COMPREHENSIVE MOVE VALIDATION using chess rules engine
        # This includes:
        # - Piece movement rules
        # - King safety (cannot leave king in check)
        # - Check escape validation (if in check, move must resolve it)
        from .chess_rules import ChessRules
        is_valid, error_msg = ChessRules.is_valid_move(
            game.board_state, 
            from_pos, 
            to_pos, 
            game.current_turn
        )
        
        if not is_valid:
            # Check if player is in check and trying invalid move
            if ChessRules.is_in_check(game.board_state, game.current_turn):
                error_msg = "You are in check! You must escape check."
            
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'message': f'Illegal move: {error_msg}'
            }))
            return
        
        # Execute move (only if validation passed)
        board = game.board_state
        piece = board[from_pos]
        
        # Handle pawn promotion
        if piece[1] == 'p':
            to_rank = int(to_pos[1])
            color_code = piece[0]
            # Check if pawn reached promotion rank
            if (color_code == 'w' and to_rank == 8) or (color_code == 'b' and to_rank == 1):
                # Promote pawn to chosen piece (default to queen if not specified)
                promote_to = promotion if promotion in ['q', 'r', 'b', 'n'] else 'q'
                piece = f"{color_code}{promote_to}"
        
        board[to_pos] = piece
        del board[from_pos]
        
        # Update game state
        next_turn = 'black' if game.current_turn == 'white' else 'white'
        move_history = list(game.move_history) if game.move_history else []
        move_history.append({'from': from_pos, 'to': to_pos, 'piece': piece, 'promotion': promotion})
        
        # CHECK FOR END-GAME CONDITIONS (checkmate, stalemate, draw)
        game_status, winner, reason = ChessRules.check_game_status(board, next_turn)
        
        # Update game in database
        if game_status in ['checkmate', 'stalemate', 'draw']:
            await self.finish_game(game.code, winner, game_status)
        else:
            await self.update_game(game.code, board, next_turn, move_history)
        
        # Broadcast move to all players
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'game_update',
            'board_state': board,
            'current_turn': next_turn,
            'move': {'from': from_pos, 'to': to_pos, 'piece': piece}
        })
        
        # Handle end-game notification
        if game_status in ['checkmate', 'stalemate', 'draw']:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_over',
                'status': game_status,
                'winner': winner,
                'reason': reason
            })
            return  # Stop here, no bot move needed
        
        # Notify if in check
        if game_status == 'check':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'check_notification',
                'color': next_turn
            })
        
        # Handle bot move if needed (completely non-blocking)
        # Bot should move when it's playing OR when it's in check (must escape)
        if game.is_bot_game and next_turn == game.bot_color and game_status in ['playing', 'check']:
            # Notify UI that bot is thinking
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'bot_thinking',
                'thinking': True
            })
            # Schedule bot move as background task (doesn't block user's move)
            import asyncio
            asyncio.create_task(self.make_bot_move(game.code))
    
    async def make_bot_move(self, game_code):
        import asyncio
        from .chess_bot import ChessBot
        from .chess_rules import ChessRules
        
        try:
            # Bot thinks for exactly 2 seconds
            await asyncio.sleep(2)
            
            game = await self.get_game_by_code(game_code)
            if not game or game.status != 'playing':
                return
            
            # Ensure it's actually the bot's turn
            if game.current_turn != game.bot_color:
                return
            
            # Get legal move from bot using current_turn (should match bot_color)
            move = ChessBot.make_move(game.board_state, game.current_turn)
        except Exception as e:
            print(f"Bot move error: {e}")
            return
        
        if not move:
            # Bot has no legal moves - check for checkmate or stalemate
            game_status, winner, reason = ChessRules.check_game_status(
                game.board_state, 
                game.current_turn
            )
            
            # Only end game if it's actually checkmate or stalemate
            if game_status in ['checkmate', 'stalemate', 'draw']:
                await self.finish_game(game_code, winner, game_status)
                
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'game_over',
                    'status': game_status,
                    'winner': winner,
                    'reason': reason
                })
            else:
                # Bot couldn't find a move but game isn't over - this shouldn't happen
                # Try to find ANY legal move as fallback
                print(f"Bot failed to find move but game status is: {game_status}")
                # Notify that bot is stuck (for debugging)
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'bot_thinking',
                    'thinking': False
                })
            return
        
        if move:
            from_pos, to_pos = move
            
            # Double-check move validity with rules engine (safety check)
            is_valid, _ = ChessRules.is_valid_move(
                game.board_state,
                from_pos,
                to_pos,
                game.current_turn
            )
            
            if not is_valid:
                # Bot generated invalid move - skip turn (shouldn't happen)
                return
            
            # Execute validated move
            board = game.board_state
            piece = board[from_pos]
            
            # Handle bot pawn promotion (always promote to queen)
            if piece[1] == 'p':
                to_rank = int(to_pos[1])
                color_code = piece[0]
                if (color_code == 'w' and to_rank == 8) or (color_code == 'b' and to_rank == 1):
                    piece = f"{color_code}q"  # Bot always promotes to queen
            
            board[to_pos] = piece
            del board[from_pos]
            
            next_turn = 'white' if game.current_turn == 'black' else 'black'
            move_history = list(game.move_history) if game.move_history else []
            move_history.append({'from': from_pos, 'to': to_pos, 'piece': piece, 'bot': True})
            
            # CHECK FOR END-GAME CONDITIONS after bot move
            game_status, winner, reason = ChessRules.check_game_status(board, next_turn)
            
            # Update game in database
            if game_status in ['checkmate', 'stalemate', 'draw']:
                await self.finish_game(game_code, winner, game_status)
            else:
                await self.update_game(game_code, board, next_turn, move_history)
            
            # Broadcast bot's move
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'game_update',
                'board_state': board,
                'current_turn': next_turn,
                'move': {'from': from_pos, 'to': to_pos, 'piece': piece, 'bot': True}
            })
            
            # Handle end-game notification
            if game_status in ['checkmate', 'stalemate', 'draw']:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'game_over',
                    'status': game_status,
                    'winner': winner,
                    'reason': reason
                })
            elif game_status == 'check':
                # Notify if bot put player in check
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'check_notification',
                    'color': next_turn
                })
    
    async def handle_resign(self):
        game = await self.get_game()
        if not game:
            return
        
        player_color = await self.get_player_color(game)
        if not player_color:
            return
        
        winner = 'black' if player_color == 'white' else 'white'
        await self.finish_game(game.code, winner)
        
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
    
    async def bot_thinking(self, event):
        await self.send(text_data=json.dumps({
            'type': 'bot_thinking',
            'thinking': event['thinking']
        }))
    
    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'status': event.get('status', 'finished'),
            'winner': event['winner'],
            'reason': event['reason']
        }))
    
    async def send_game_state(self):
        game = await self.get_game()
        if game:
            player_color = await self.get_player_color(game)
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'board_state': game.board_state,
                'current_turn': game.current_turn,
                'is_bot_game': game.is_bot_game,
                'bot_color': game.bot_color,
                'player_color': player_color,
                'status': game.status
            }))
    
    @database_sync_to_async
    def get_game(self):
        try:
            return ChessGame.objects.get(code=self.game_code)
        except ChessGame.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_game_by_code(self, code):
        try:
            return ChessGame.objects.get(code=code)
        except ChessGame.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_player_color(self, game):
        if game.white_player_id == self.user.id:
            return 'white'
        elif game.black_player_id == self.user.id:
            return 'black'
        # For bot games, if user is white player
        elif game.is_bot_game and game.white_player_id == self.user.id:
            return 'white'
        return None
    
    @database_sync_to_async
    def update_game(self, code, board_state, current_turn, move_history):
        game = ChessGame.objects.get(code=code)
        game.board_state = board_state
        game.current_turn = current_turn
        game.move_history = move_history
        game.save()
    
    @database_sync_to_async
    def finish_game(self, code, winner, status='finished'):
        game = ChessGame.objects.get(code=code)
        game.status = status if status in ['checkmate', 'stalemate', 'draw'] else 'finished'
        game.winner = winner
        game.save()
    
    async def check_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'check',
            'color': event['color']
        }))
