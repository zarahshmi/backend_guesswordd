from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import RegisterAPIView, CreateGameAPIView, WaitingGamesAPIView, JoinGameAPIView, GuessLetterAPIView, \
    PauseGameAPIView, ResumeGameAPIView, ProfileAPIView, HistoryAPIView, LeaderboardAPIView, CancelGameAPIView, \
    GameStatusAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('profile/', ProfileAPIView.as_view(), name='profile'),

    path('create-game/', CreateGameAPIView.as_view(), name='create_game'),
    path('waiting-games/', WaitingGamesAPIView.as_view(), name='waiting_games'),
    path("games/<int:game_id>/join/", JoinGameAPIView.as_view(), name='join_game'),

    path('games/<int:game_id>/guess/', GuessLetterAPIView.as_view(), name='guess_letter'),
    path('games/<int:game_id>/cancel/', CancelGameAPIView.as_view(), name='cancel_game'),
    path('games/<int:game_id>/status/', GameStatusAPIView.as_view(), name='game_status'),
    path('games/<int:game_id>/pause/', PauseGameAPIView.as_view(), name='pause_game'),
    path('games/<int:game_id>/resume/', ResumeGameAPIView.as_view(), name='resume_game'),


    path('history/', HistoryAPIView.as_view(), name='game-history'),
    path('leaderboard/', LeaderboardAPIView.as_view(), name='leaderboard'),

]


