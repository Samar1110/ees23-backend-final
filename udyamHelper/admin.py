from django.contrib import admin

# Register your models here.
from .models import Team, Event, NoticeBoard
admin.site.register(Team)
admin.site.register(Event)
admin.site.register(NoticeBoard)

