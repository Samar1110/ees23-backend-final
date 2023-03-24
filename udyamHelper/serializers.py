from rest_framework import serializers
from .models import Event, Team, NoticeBoard
from customauth.models import UserAcount

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    event = serializers.CharField()
    leader = serializers.EmailField()
    member1 = serializers.EmailField(required = False, allow_null = True, allow_blank=True)
    member2 = serializers.EmailField(required = False, allow_null = True, allow_blank=True)


    def save(self, **kwargs):
        data = self.validated_data
        teamname = data["teamname"]
        event = Event.objects.get(event = data["event"])
        leader = UserAcount.objects.get(email = data["leader"])
        member1 = (
            UserAcount.objects.get(email=data["member1"]) if data["member1"] else None
        )
        member2 = (
            UserAcount.objects.get(email=data["member2"]) if data["member2"] else None
        )

        team = Team.objects.create(
            teamname = teamname,
            event = event,
            leader = leader,
            member1 = member1,
            member2 = member2,
        )
        return team
    
    class Meta:
        model = Team
        fields = [
            "teamname",
            "event",
            "leader",
            "member1",
            "member2",
        ]
        
class NoticeBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeBoard
        fields = "__all__"
