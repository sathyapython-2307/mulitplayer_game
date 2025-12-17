from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_code>\w+)/$', consumers.GameConsumer.as_asgi()),
    re_path(r'ws/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),
    re_path(r'ws/chess/matchmaking/$', consumers.ChessConsumer.as_asgi()),
    re_path(r'ws/chess/(?P<game_code>\w+)/$', consumers.ChessConsumer.as_asgi()),
]
