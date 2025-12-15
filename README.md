# Real-Time Multiplayer Gaming Platform

A modern Django-based gaming platform with WebSocket integration for real-time multiplayer experiences.

## Features
- Player matchmaking system
- Live game rooms with real-time updates
- In-game chat functionality
- Game state synchronization
- Responsive design with warm color theme

## Setup
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## WebSocket Support
For production, use Redis as the channel layer backend.
