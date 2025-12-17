from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.contrib import messages
from .models import GameRoom, PlayerStats, ChessGame

def home(request):
    return render(request, 'games/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            PlayerStats.objects.create(user=user)
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def game_selection(request):
    if not hasattr(request.user, 'stats'):
        PlayerStats.objects.create(user=request.user)
    return render(request, 'games/game_selection.html')

@login_required
def lobby(request):
    rooms = GameRoom.objects.filter(status='waiting').order_by('-created_at')
    if not hasattr(request.user, 'stats'):
        PlayerStats.objects.create(user=request.user)
    return render(request, 'games/lobby.html', {'rooms': rooms})

@login_required
def matchmaking(request):
    room = GameRoom.objects.filter(status='waiting').exclude(host=request.user).first()
    if room and room.players.count() < room.max_players:
        room.players.add(request.user)
        return redirect('game_room', code=room.code)
    return render(request, 'games/matchmaking.html')

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name', f"{request.user.username}'s Room")
        max_players = int(request.POST.get('max_players', 4))
        room = GameRoom.objects.create(host=request.user, name=name, max_players=max_players)
        room.players.add(request.user)
        return redirect('game_room', code=room.code)
    return render(request, 'games/create_room.html')

@login_required
def join_room(request, code):
    room = get_object_or_404(GameRoom, code=code)
    if room.players.count() < room.max_players:
        room.players.add(request.user)
    return redirect('game_room', code=code)

@login_required
def game_room(request, code):
    room = get_object_or_404(GameRoom, code=code)
    return render(request, 'games/game_room.html', {'room': room})

@login_required
def leave_room(request, code):
    room = get_object_or_404(GameRoom, code=code)
    room.players.remove(request.user)
    if room.host == request.user:
        if room.players.exists():
            room.host = room.players.first()
            room.save()
        else:
            room.delete()
            return redirect('lobby')
    return redirect('lobby')


def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required
def chess_lobby(request):
    active_games = ChessGame.objects.filter(status='playing').order_by('-created_at')[:10]
    return render(request, 'games/chess_lobby.html', {'active_games': active_games})

@login_required
def chess_matchmaking(request):
    return render(request, 'games/chess_matchmaking.html')

@login_required
def chess_game(request, code):
    from .models import ChessGame
    game = get_object_or_404(ChessGame, code=code)
    
    # Determine player color
    player_color = None
    opponent = None
    if game.white_player == request.user:
        player_color = 'white'
        opponent = game.black_player.username if game.black_player else 'Bot'
    elif game.black_player == request.user:
        player_color = 'black'
        opponent = game.white_player.username if game.white_player else 'Bot'
    
    return render(request, 'games/chess_game.html', {
        'game': game,
        'player_color': player_color,
        'opponent': opponent
    })
