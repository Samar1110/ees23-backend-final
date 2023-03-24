from .models import Team, Event, NoticeBoard
from rest_framework.response import Response
from .serializers import EventSerializer, TeamSerializer, NoticeBoardSerializer
from customauth.models import UserAcount
from rest_framework import serializers,generics, permissions, status
from rest_framework import permissions
from django.utils.datastructures import MultiValueDictKeyError
import xlwt
import pandas as pd
import shutil
import sys
from django.http import HttpResponse
from django.http import Http404
from rest_framework.decorators import api_view, renderer_classes



class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        name = serializers.CharField(required=True)
        college_name = serializers.CharField(required=True)
        year = serializers.CharField(required=True)
        phone_number = serializers.CharField(required=True)

def checks(request):
    try:
        event = Event.objects.get(event=request.data["event"])
        leader = UserAcount.objects.get(email=request.data["leader"])
        member1 = (
            UserAcount.objects.get(email=request.data["member1"])
            if request.data["member1"]
            else None
        )
        member2 = (
            UserAcount.objects.get(email=request.data["member2"])
            if request.data["member2"]
            else None
        )
        event_teams = Team.objects.filter(event=event)
        first_yearites = 0
        second_yearites = 0
        if leader.year == "FIRST":
            first_yearites += 1
        elif leader.year == "SECOND":
            second_yearites += 1
        if member2:
            if member2.year == "FIRST":
                first_yearites += 1
            elif member2.year == "SECOND":
                second_yearites += 1
        if member1:
            if member1.year == "FIRST":
                first_yearites += 1
            elif member1.year == "SECOND":
                second_yearites += 1
    except Event.DoesNotExist:
        return "Event does not exist"
    except UserAcount.DoesNotExist:
        return "User does not exist"

    if (
        request.data["leader"] == request.data["member1"]
        or request.data["leader"] == request.data["member2"]
        or (
            request.data["member1"] == request.data["member2"]
            and request.data["member1"] != ""
        )
    ):
        return "Single user cannot be present twice in the team"
    elif leader != request.user and member1 != request.user and member2 != request.user:
        return "Requesting user must be a member of the team. Cannot create a team which you are not a part of."
    elif Team.objects.filter(teamname=request.data["teamname"], event=event).count():
        return "Team name already taken"
    elif (
        event_teams.filter(leader=leader).count()
        or event_teams.filter(member1=leader).count()
        or event_teams.filter(member2=leader).count()
    ):
        return "Leader already has a team in this event"
    elif (
        event_teams.filter(leader=member1).count()
        or event_teams.filter(member1=member1).count()
        or event_teams.filter(member2=member1).count()
    ) and member1 is not None:
        return "Member 1 already has a team in this event"
    elif (
        event_teams.filter(leader=member2).count()
        or event_teams.filter(member1=member2).count()
        or event_teams.filter(member2=member2).count()
    ) and member2 is not None:
        return "Member 2 already has a team in this event"
    elif (
        second_yearites != 0
        and first_yearites + second_yearites > event.members_after_1st_year
    ):
        return (
            "Max size of a not-all-1st-yearites team is "
            + str(event.members_after_1st_year)
            + " for this event"
        )
    elif second_yearites == 0 and first_yearites > event.members_from_1st_year:
        return (
            "Max size of a all-1st-yearites team is "
            + str(event.members_from_1st_year)
            + " for this event"
        )


class ViewAllEvent(generics.ListAPIView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

class TeamCreateView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TeamSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = checks(request)
        if message:
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()
        team = Team.objects.get(
            teamname=request.data["teamname"],
            event=Event.objects.get(event=request.data["event"]),
        )
        team_info = {
            "teamname": team.teamname,
            "event": team.event.event,
            "leader": team.leader.email,
            "member1": team.member1.email if team.member1 else None,
            "member2": team.member2.email if team.member2 else None,
        }

        return Response(team_info, status=status.HTTP_200_OK)

class TeamCountView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class=TeamSerializer

    def get(self, request):
        res = {}
        for event in Event.objects.all():
            teams = Team.objects.filter(event=event)
            res[event.event] = teams.count()
        return Response(res, status=status.HTTP_200_OK)
    
class GetAllNoticeView(generics.RetrieveAPIView):
    serializer_class = NoticeBoardSerializer
    queryset = NoticeBoard.objects.all()
    def get(self, request, event):
        if( event == "all"):
            eventslist = self.queryset.all()
        else :
            eventslist = self.queryset.filter(event=event)
            
        context=[]
        for event in eventslist:
            context.append({
                "title": event.title,
                "description": event.description,
                "date": event.date,
                "link": event.link,
            })
        return Response(context, status=status.HTTP_200_OK)
    

        
            
class TeamGetUserView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TeamSerializer

    def appendTeam(self, teams, event_teams):
        for team in teams:
            team_info = {
                "id": team.id,
                "teamname": team.teamname,
                "event": team.event.event,
                "leader": team.leader.email,
                "member1": team.member1.email if team.member1 else None,
                "member2": team.member2.email if team.member2 else None,
            }
            event_teams.append(team_info)

    def get(self, request):
        try:
            teams_as_leader = Team.objects.filter(leader=request.user)
            teams_as_member1 = Team.objects.filter(member1=request.user)
            teams_as_member2 = Team.objects.filter(member2=request.user)
            event_teams = []
            self.appendTeam(teams_as_leader, event_teams)
            self.appendTeam(teams_as_member1, event_teams)
            self.appendTeam(teams_as_member2, event_teams)
            return Response(event_teams, status=status.HTTP_200_OK)
        except UserAcount.DoesNotExist:
            return Response(
                {"error": "No such user exists"}, status=status.HTTP_404_NOT_FOUND
            )



@api_view(('GET',))
def export_users_xls(request):
    if not request.user.has_perm("view_useracount") :
        raise Http404
    
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="UserAccounts.xls"'

    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("User Accounts")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ["Name", "Email", "Year", "College", "Radianite Points"]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = UserAcount.objects.all().values_list(
        "name", "email", "year", "college_name", "radianite_points"
    )
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response



@api_view(('GET',))
def export_teams_xls(request):
    if not request.user.has_perm("view_useracount") :
        raise Http404

    # print(request.user)
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="Teams.xls"'

    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Teams")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ["Team Event", "Team Name", "Leader Name","Leader Email","Leader Phone Number", "Member1 Name", "Member1 Email", "Member1 Phone Number", "Member2 Name", "Member2 Email", "Member2 Phone Number"]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = []
    for team in Team.objects.order_by("-event"):
        rows.append(
            [team.event.event, team.teamname, team.leader.name, team.leader.email, team.leader.phone_number, team.member1.name if(team.member1) else " ", team.member1.email if(team.member1) else " ", team.member1.phone_number if(team.member1) else " ", team.member2.name if(team.member2) else " ", team.member2.email if(team.member2) else " ", team.member2.phone_number if(team.member2) else " "]
        )

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def checks2(request):
    try:
        # teamname=request.data["teamname"]
        
        # print(request.data)
        event = Event.objects.get(event=request.data["event"])
        leader = UserAcount.objects.get(email=request.data["leader"])
        try:
            teamname=Team.objects.filter(event=event,leader=leader)[0].teamname
        except:
            return "Team Does Not Exist"

        
        member1 = (
            UserAcount.objects.get(email=request.data["member1"])
            if request.data["member1"]
            else None
        )
        member2 = (
            UserAcount.objects.get(email=request.data["member2"])
            if request.data["member2"]
            else None
        )
        # print(event)
        # print(teamname)
        # print(request.data["teamname"])
        # print(leader)
        # print(member1)
        # print(member2)

        event_teams = Team.objects.filter(event=event)
        first_yearites = 0
        second_yearites = 0
        if leader.year == "FIRST":
            first_yearites += 1
        elif leader.year == "SECOND":
            second_yearites += 1
        if member2:
            if member2.year == "FIRST":
                first_yearites += 1
            elif member2.year == "SECOND":
                second_yearites += 1
        if member1:
            if member1.year == "FIRST":
                first_yearites += 1
            elif member1.year == "SECOND":
                second_yearites += 1
    except Event.DoesNotExist:
        return "Event does not exist"
    except UserAcount.DoesNotExist:
        return "User does not exist"
    
    if (
        request.data["leader"] == request.data["member1"]
        or request.data["leader"] == request.data["member2"]
        or (
            request.data["member1"] == request.data["member2"]
            and request.data["member1"] != ""
        )
    ):
        return "Single user cannot be present twice in the team"
    elif leader != request.user and member1 != request.user and member2 != request.user:
        return "Requesting user must be a member of the team. Cannot edit a team which you are not a part of."
    elif teamname != request.data["teamname"]:
        if(Team.objects.filter(teamname=request.data["teamname"]).count()!=0):
            return "Same Name team already exists."
    elif member1!=None and request.data["member1"]==None:
        return "Member1 Name cannot be an empty string"
    elif member2!=None and request.data["member2"]==None:
        return "Member2 Name cannot be an empty string"
    elif (
        (event_teams.filter(leader=member1).count() and event_teams.filter(leader=member1)[0].leader!=leader )
        or (event_teams.filter(member1=member1).count() and event_teams.filter(member1=member1)[0].leader!=leader )
        or (event_teams.filter(member2=member1).count() and event_teams.filter(member2=member1)[0].leader!=leader )
    ) and member1 is not None:
        return "Member 1 already has a team in this event"
    elif (
        (event_teams.filter(leader=member2).count() and event_teams.filter(leader=member2)[0].leader!=leader )
        or (event_teams.filter(member1=member2).count() and event_teams.filter(member1=member2)[0].leader!=leader )
        or (event_teams.filter(member2=member2).count() and event_teams.filter(member2=member2)[0].leader!=leader )
    ) and member2 is not None:
        return "Member 2 already has a team in this event"
    elif (
        second_yearites != 0
        and first_yearites + second_yearites > event.members_after_1st_year
    ):
        return (
            "Max size of a not-all-1st-yearites team is "
            + str(event.members_after_1st_year)
            + " for this event"
        )
    elif second_yearites == 0 and first_yearites > event.members_from_1st_year:
        return (
            "Max size of a all-1st-yearites team is "
            + str(event.members_from_1st_year)
            + " for this event"
        )


class TeamView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TeamSerializer

    def teamInfo(self, team):
        team_info = {
            "teamname": team.teamname,
            "event": team.event.event,
            "leader": team.leader.email,
            "member1": team.member1.email if team.member1 else None,
            "member2": team.member2.email if team.member2 else None,
        }
        return team_info

    def get(self, request, id):
        try:
            team = Team.objects.get(id=id)
            return Response(self.teamInfo(team), status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, id):
        try:
            team = Team.objects.get(id=id)
            event = Event.objects.get(event=request.data["event"])
            leader = UserAcount.objects.get(email=request.data["leader"])
            team.teamname = request.data["teamname"]
            team.event = event
            team.leader = leader
            team.member1 = (
                UserAcount.objects.get(email=request.data["member1"])
                if request.data["member1"] != ""
                else None
            )
            team.member2 = (
                UserAcount.objects.get(email=request.data["member2"])
                if request.data["member2"] != ""
                else None
            )
            # print("HEllo1")
            message = checks2(request)
            # print("HEllo2")
         
            if message and message != "Team name already taken":
                return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)
            # print("HEllo3")
            team.save()
            # print("HEllo7")
            serializer = self.get_serializer(data=request.data)
            # print("HEllo8")
            serializer.is_valid(raise_exception=False)
            team_info = {
            "teamname": team.teamname,
            "event": team.event.event,
            "leader": team.leader.email,
            "member1": team.member1.email if team.member1 else None,
            "member2": team.member2.email if team.member2 else None,
            }
            # print("HEllo4")
            return Response(team_info, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            # print("HEllo5")
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except UserAcount.DoesNotExist:
            return Response(
                {"error": "User account not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, id):
        if Team.objects.filter(id=id).count():
            team = Team.objects.get(id=id)
            if (
                request.user == team.leader
            ):
                team.delete()
                return Response(
                    {"message": "Team deleted successfully"}, status=status.HTTP_200_OK
                )
            return Response(
                {"error": "Only a team member is allowed to delete his/her team."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
