from django.contrib.auth.models import AbstractUser
from django.db import models



class Player(AbstractUser):
    level = models.PositiveSmallIntegerField(default=1)
    xp = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Player'
        verbose_name_plural = 'Players'



class Word(models.Model):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'),
    ]

    text = models.CharField(max_length=64)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return f'{self.text} ({self.difficulty})'



class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for player'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('finished', 'Finished'),
    ]

    player1 = models.ForeignKey('Player', related_name='games_created', on_delete=models.CASCADE)
    player2 = models.ForeignKey('Player', related_name='games_joined', on_delete=models.CASCADE, null=True, blank=True)
    player1_score = models.PositiveSmallIntegerField(default=0)
    player2_score = models.PositiveSmallIntegerField(default=0)
    word = models.CharField(max_length=64)
    masked_word = models.CharField(max_length=64)
    difficulty = models.CharField(max_length=10, choices=Word.DIFFICULTY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    turn = models.ForeignKey('Player', related_name='turns', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Game #{self.pk} - {self.status}'



class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='guesses')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    letter = models.CharField(max_length=1)
    correct = models.BooleanField()
    guessed_at = models.DateTimeField(auto_now_add=True)