from rest_framework import serializers
from .models import Game, Player, Word
from django.db.models import Q

class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(source='player1.username')
    player2 = serializers.CharField(source='player2.username', allow_null=True)
    current_turn = serializers.CharField(source='turn.username', allow_null=True)
    player1_score = serializers.SerializerMethodField()
    player2_score = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'player1', 'player2', 'masked_word',
                  'difficulty', 'status', 'created_at', 'started_at',
                  'current_turn', 'player1_score', 'player2_score']
        read_only_fields = ['player1_score', 'player2_score']

    def get_player1_score(self, obj):
        return obj.player1_score

    def get_player2_score(self, obj):
        return obj.player2_score if obj.player2 else 0







class GameCreateSerializer(serializers.Serializer):
    difficulty = serializers.ChoiceField(choices=['easy', 'medium', 'hard'])




class WaitingGameSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(source='player1.username')
    word_length = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'player1', 'difficulty', 'created_at', 'status', 'word_length']

    def get_word_length(self, obj):
        return len(obj.word)




class GameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'




class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'username', 'email', 'score', 'level', 'xp']
        read_only_fields = ['score', 'level', 'xp']




class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = '__all__'




class ProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    score = serializers.IntegerField(read_only=True)
    games_played = serializers.SerializerMethodField()
    wins = serializers.SerializerMethodField()
    losses = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    def get_games_played(self, obj):
        return getattr(obj, 'games_played', 0)

    def get_wins(self, obj):
        return getattr(obj, 'wins', 0)

    def get_losses(self, obj):
        return getattr(obj, 'losses', 0)

    def get_win_rate(self, obj):
        return getattr(obj, 'win_rate', "0.0%")

    def get_rank(self, obj):
        players = Player.objects.order_by('-score')
        rank = list(players.values_list('id', flat=True)).index(obj.id) + 1
        return rank



class GameHistorySerializer(serializers.ModelSerializer):
    opponent = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    started_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    your_score = serializers.SerializerMethodField()
    opponent_score = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'difficulty', 'status', 'masked_word', 'started_at',
                  'opponent', 'result', 'your_score', 'opponent_score']
        read_only_fields = fields

    def get_opponent(self, obj):
        user = self.context['request'].user
        if obj.player1 == user:
            return obj.player2.username if obj.player2 else "AI"
        return obj.player1.username

    def get_result(self, obj):
        user = self.context['request'].user
        if obj.status != 'finished':
            return None

        player1 = obj.player1
        player2 = obj.player2

        # امتیازهای همان بازی
        p1_score = obj.player1_score
        p2_score = obj.player2_score

        if p1_score > p2_score:
            return 'win' if user == player1 else 'lose'
        elif p2_score > p1_score:
            return 'win' if user == player2 else 'lose'
        return 'draw'

    def get_your_score(self, obj):
        user = self.context['request'].user
        if obj.player1 == user:
            return obj.player1_score
        elif obj.player2 == user:
            return obj.player2_score
        return 0

    def get_opponent_score(self, obj):
        user = self.context['request'].user
        if obj.player1 == user:
            return obj.player2_score if obj.player2 else 0
        elif obj.player2 == user:
            return obj.player1_score
        return 0




class LeaderboardSerializer(serializers.ModelSerializer):
    win_rate = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id', 'username', 'score', 'level', 'xp', 'win_rate', 'rank']
        read_only_fields = fields

    def get_win_rate(self, obj):

        finished_games = Game.objects.filter(
            (Q(player1=obj) | Q(player2=obj)) &
            Q(status='finished')
        )
        total_games = finished_games.count()

        wins = 0
        for game in finished_games:
            player1 = game.player1
            player2 = game.player2 if game.player2 else obj

            if game.player1_score > game.player2_score and player1 == obj:
                wins += 1
            elif game.player2_score > game.player1_score and player2 == obj:
                wins += 1


        if total_games > 0:
            return f"{round((wins / total_games) * 100, 2)}%"
        return "0%"

    def get_rank(self, obj):

        players = list(Player.objects.order_by('-score').values_list('id', flat=True))
        return players.index(obj.id) + 1