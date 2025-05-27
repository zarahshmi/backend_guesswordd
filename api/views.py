from django.db.models import Q,F
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from api.models import Player, Word, Game, Guess
import random
from django.utils import timezone
from api.serializers import GameCreateSerializer, WaitingGameSerializer, GameSerializer, GameListSerializer, \
    ProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from api.serializers import GameHistorySerializer, LeaderboardSerializer,GameSerializer
from rest_framework import status




class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {
                    'error': 'Username and password are required!'
                }, status=400
            )

        if Player.objects.filter(username=username).exists():
            return Response(
                {
                    'error': 'This username has already been taken!'
                }, status=400
            )
        player = Player.objects.create_user(
            username=username,
            password=password
        )

        return Response(
            {
                'success': True,
                'user': {
                    'id': player.id,
                    'username': player.username
                }
            }, status=201
        )




class CreateGameAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GameCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        difficulty = serializer.validated_data['difficulty']
        words = Word.objects.filter(difficulty=difficulty)

        if not words.exists():
            return Response({'error': 'No words found for this difficulty'}, status=400)

        word_obj = random.choice(list(words))
        real_word = word_obj.text.lower()
        masked_word = '_' * len(real_word)


        game = Game.objects.create(
            player1=request.user,
            word=real_word,
            masked_word=masked_word,
            difficulty=difficulty,
            status='waiting',
            turn=request.user
        )

        return Response({
            'game_id': game.id,
            'word_length': len(real_word),
            'difficulty': game.difficulty,

        }, status=201)




class WaitingGamesAPIView(APIView):
    serializer_class = WaitingGameSerializer
    permission_classes = [IsAuthenticated]


    def get(self, request):
        user = request.user

        games = Game.objects.filter(
            Q(status='waiting', player2__isnull=True) |
            Q(status='active', player1=user) |
            Q(status='active', player2=user)
        )

        serializer = self.serializer_class(games, many=True, context={'request': request})
        return Response(serializer.data)



class JoinGameAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id, *args, **kwargs):
        game = get_object_or_404(Game, id=game_id)

        if game.status != 'waiting':
            return Response({'error': 'You cannot join this game'}, status=400)

        if game.player1 == request.user:
            return Response({'error': 'You cannot join your own game'}, status=400)

        if game.player2:
            return Response({'error': 'Game already has two players'}, status=400)

        game.player2 = request.user
        game.status = 'active'
        game.started_at = timezone.now()

        game.turn = random.choice([game.player1, game.player2])
        game.save()

        serializer = GameSerializer(game)
        return Response(serializer.data, status=200)





class GuessLetterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        letter = request.data.get('letter', '').lower()
        if not letter or len(letter) != 1 or not letter.isalpha():
            return Response({'error': 'Invalid letter'}, status=400)

        game = get_object_or_404(Game, id=game_id)

        if game.status != 'active':
            return Response({'error': 'Game is not active'}, status=400)

        if game.turn != request.user:
            return Response({'error': 'It is not your turn'}, status=403)

        if game.guesses.filter(letter=letter).exists():
            return Response({'error': 'Letter already guessed'}, status=400)

        real_word = game.word
        masked = list(game.masked_word)
        correct = False

        for i, c in enumerate(real_word):
            if c == letter:
                masked[i] = letter
                correct = True

        Guess.objects.create(game=game, player=request.user, letter=letter, correct=correct)

        game.masked_word = ''.join(masked)

        is_player1 = (game.player1 == request.user)

        if correct:
            if is_player1:
                game.player1_score += 20
            else:
                game.player2_score += 20
        else:
            if is_player1:
                game.player1_score = max(0, game.player1_score - 20)
            else:
                game.player2_score = max(0, game.player2_score - 20)

        if game.masked_word == game.word:
            game.status = 'finished'

            if game.player1_score > game.player2_score:
                game.turn = game.player1  # برنده بازی
            elif game.player2_score > game.player1_score:
                game.turn = game.player2
            else:
                game.turn = None  # مساوی

            # بروزرسانی امتیاز و XP بازیکنان
            player1 = game.player1
            player2 = game.player2

            # افزودن امتیاز بازی به امتیاز کلی بازیکنان
            player1.score += game.player1_score
            player2_score = game.player2_score if player2 else 0
            if player2:
                player2.score += player2_score

            # بروزرسانی XP و بررسی سطح
            # مثلاً هر 100 XP سطح یک درجه افزایش می‌یابد
            def update_player_level(player, gained_xp):
                player.xp += gained_xp
                while player.xp >= 100:
                    player.xp -= 100
                    player.level += 1

            update_player_level(player1, game.player1_score)
            if player2:
                update_player_level(player2, player2_score)

            player1.save()
            if player2:
                player2.save()

        else:
            game.turn = game.player2 if game.turn == game.player1 else game.player1

        game.save()

        your_game_score = game.player1_score if is_player1 else game.player2_score

        return Response({
            'masked_word': game.masked_word,
            'correct': correct,
            'next_turn': game.turn.username if game.status != 'finished' and game.turn else None,
            'game_status': game.status,
            'your_score': your_game_score
        })



class PauseGameAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)

        if request.user != game.player1 and request.user != game.player2:
            return Response({'error': 'You are not part of this game'}, status=403)

        if game.status != 'active':
            return Response({'error': 'Game is not active'}, status=400)

        game.status = 'paused'
        game.save()
        return Response({'message': 'Game paused'}, status=200)





class ResumeGameAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)

        if request.user != game.player1 and request.user != game.player2:
            return Response({'error': 'You are not part of this game'}, status=403)

        if game.status != 'paused':
            return Response({'error': 'Game is not paused'}, status=400)

        game.status = 'active'
        game.save()
        return Response({'message': 'Game resumed'}, status=200)




class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        finished_games = Game.objects.filter(
            (Q(player1=user) | Q(player2=user)) & Q(status='finished')
        )

        total_games = finished_games.count()
        wins = 0
        losses = 0

        for game in finished_games:
            if game.player1_score > game.player2_score:
                if user == game.player1:
                    wins += 1
                else:
                    losses += 1
            elif game.player2_score > game.player1_score:
                if user == game.player2:
                    wins += 1
                else:
                    losses += 1
            else:
                # مساوی حساب میشه، اگر خواستی اضافه کن
                pass

        win_rate = round((wins / total_games) * 100, 2) if total_games > 0 else 0.0

        user.games_played = total_games
        user.wins = wins
        user.losses = losses
        user.win_rate = f"{win_rate}%"

        serializer = ProfileSerializer(user)
        return Response(serializer.data)




# class GameDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, game_id):
#         user = request.user
#         game = get_object_or_404(Game, id=game_id)
#
#         if game.player1 != user and game.player2 != user:
#             return Response({'detail': 'شما به این بازی دسترسی ندارید.'}, status=status.HTTP_403_FORBIDDEN)
#
#         serializer = GameSerializer(game)
#         return Response(serializer.data)



class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        games = Game.objects.filter(Q(player1=user) | Q(player2=user)).order_by('-started_at')
        serializer = GameHistorySerializer(games, many=True, context={'request': request})
        return Response(serializer.data)




class LeaderboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_players = Player.objects.order_by('-score', '-xp')[:10]
        serializer = LeaderboardSerializer(top_players, many=True)
        return Response(serializer.data)

