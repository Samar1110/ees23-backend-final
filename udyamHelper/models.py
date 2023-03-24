from django.db import models
from customauth.models import  UserAcount

class Event(models.Model):
    event = models.CharField(max_length=100, unique=True)
    members_from_1st_year = models.IntegerField()
    members_after_1st_year = models.IntegerField()

    def __str__(self):
        return self.event
  
  
EVENTS = (
    ("Mashal", "Mashal"),
    ("Udgam", "Udgam"),
    ("Udyam", "Udyam"),
)
  
class NoticeBoard(models.Model):
    title = models.TextField(blank=False, null=False, unique=True)
    description = models.TextField(blank=False, null=False)
    date = models.DateField(auto_now=True)
    link = models.TextField(blank=False, null=False)
    event = models.CharField(choices=EVENTS, max_length=20, blank=False, null=False)
    def __str__(self):
        return f"{self.event} - {self.title}"


class Team(models.Model):
    teamname = models.CharField(max_length=50, unique=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    leader = models.ForeignKey(UserAcount, on_delete=models.CASCADE)
    member1 = models.ForeignKey(UserAcount, on_delete=models.CASCADE, null=True, blank=True, related_name='member1')
    member2 = models.ForeignKey(UserAcount, on_delete=models.CASCADE, null=True, blank=True, related_name='member2')

    def __str(self):
        return f"{self.event} - {self.teamname}"
