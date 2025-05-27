from django.contrib import admin

from api.models import Player, Word, Game, Guess

# Register your models here.
admin.site.register(Player)
admin.site.register(Word)
admin.site.register(Game)
admin.site.register(Guess)

