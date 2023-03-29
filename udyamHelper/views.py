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
from PIL import ImageDraw, Image, ImageFont, ImageFile
from wsgiref.util import FileWrapper
import os
import pickle
import pyAesCrypt
from decouple import config
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from customauth.models import UserAcount
from pathlib import Path
from customauth.views import populate_googlesheet_with_team_data,populate_googlesheet_with_eventTeam_data,populate_googlesheet_with_collegteam_data


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
        populate_googlesheet_with_team_data()
        populate_googlesheet_with_eventTeam_data()
        populate_googlesheet_with_collegteam_data()
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
BASE_DIR = Path(__file__).resolve().parent.parent

# bufferSize = 64 * 1024
# password = config('SERVICE_ACCOUNT_DECRYPT_KEY')
spreadsheet_id = config('SPREADSHEET_ID',default="1c2dfhdeDRaa-i369P6wvMVA8vWmsvuSn_zLlM01VxYc")

# def decrypt_file(filename):
#     with open(os.path.join(BASE_DIR, f"{filename}.aes"), "rb") as encrypted_file:
#         with open(os.path.join(BASE_DIR, filename), "wb") as decrypted_file:
#             encFileSize = os.stat(os.path.join(BASE_DIR, f"{filename}.aes")).st_size
#             # decrypt file stream
#             pyAesCrypt.decryptStream(
#                 encrypted_file,
#                 decrypted_file,
#                 password,
#                 bufferSize,
#                 encFileSize
#             )

# def encrypt_file(filename):
#     with open(os.path.join(BASE_DIR, filename), "rb") as decrypted_file:
#         with open(os.path.join(BASE_DIR, f"{filename}.aes"), "wb") as encrypted_file:
#             pyAesCrypt.encryptStream(decrypted_file, encrypted_file, password, bufferSize)
            
class UsersSheet:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    RANGE_NAME = 'Registration'
    value_input_option = 'USER_ENTERED'

    creds = None
       
    service_account_file = 'excelsheet-381920-4c0c0a0a6e7a.json'
    creds = None
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    @classmethod
    def get_user_row(cls, user):
        result = cls.sheet.values().get(spreadsheetId=spreadsheet_id, range=cls.RANGE_NAME).execute()
        rows = result.get('values', [])
        for i in  range(len(rows)):
            if rows[i][1] == user.email:
                return i+1
        return len(rows)+1

    @classmethod
    def get_user_data(cls,user):
        row=[]
        try:
            row.append(user.name)
            row.append(user.email)
            row.append(user.year)
            row.append(user.college_name)
            row.append(user.radianite_points)
        except:
            for i in range(5): row.append("")

        row.append("Yes" if user.is_active else "No")
        return row

    @classmethod
    def initialize_spreadsheet(cls):
        values = []
        for user in UserAcount.objects.all().order_by('id'):
            values.append(cls.get_user_data(user))

        body = {
            'values': values
        }
        result = cls.service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=cls.RANGE_NAME+"!A2:O10000").execute()
        result = cls.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=cls.RANGE_NAME, valueInputOption=cls.value_input_option, body=body).execute()

    @classmethod
    def update_user(cls, email):
        user=UserAcount.objects.get(email=email)
        row = cls.get_user_row(user)
        values = [cls.get_user_data(user)]
        body = {
            'values': values
        }
        result = cls.service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=cls.RANGE_NAME+f"!A{row}", valueInputOption=cls.value_input_option, body=body).execute()

    @classmethod
    def new_user(cls, user):
        values = [cls.get_user_data(user)]
        body = {
            'values': values
        }
        result = cls.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=cls.RANGE_NAME, valueInputOption=cls.value_input_option, body=body).execute()



def checks2(request):
    try:
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
            
            message = checks2(request)
         
            if message and message != "Team name already taken":
                return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)
            team.save()
            populate_googlesheet_with_team_data()
            populate_googlesheet_with_eventTeam_data()
            populate_googlesheet_with_collegteam_data()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=False)
            team_info = {
            "teamname": team.teamname,
            "event": team.event.event,
            "leader": team.leader.email,
            "member1": team.member1.email if team.member1 else None,
            "member2": team.member2.email if team.member2 else None,
            }
            return Response(team_info, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
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


def createCerti(email):
    df = pd.read_csv("static/results.csv")
    userfont0 = ImageFont.truetype("static/Aller_Rg.ttf", 15)
    userfont = ImageFont.truetype("static/Aller_Rg.ttf", 33)
    userfont1 = ImageFont.truetype("static/Aller_Rg.ttf", 44)
    os.makedirs("static/certificates")
    for index, j in df.iterrows():
        if str(j["Email"]).replace(" ", "") == email:
            img = Image.open("static/template/{}.png".format(j["Certificate"]))
            name_coord = {
                "EES_Appreciation_Coordinator": (1100, 598),
                "EES_Appreciation_Core": (1100, 595),
                "EES_Appreciation_Core_2": (1100, 595),
                "EES_Merit": (1110, 595),
                "EES_Participation": (1140, 600),
                "Udyam_Appreciation": (680, 388),
                "Udyam_Appreciation_2": (680, 388),
                "Udyam_Merit": (757, 386),
                "Udyam_Participation": (760, 390),
            }
            draw = ImageDraw.Draw(img)
            draw.text(
                xy=name_coord.get(j["Certificate"]),
                text="{}".format(j["Name"]),
                fill=(0, 0, 0),
                font=userfont if j["Certificate"][0] == "U" else userfont1,
            )
            draw.text(
                xy=(1150, 2) if j["Certificate"][0] == "U" else (1735, 4),
                text="{}".format(j["Serial Number"]),
                fill=(0, 0, 0),
                font=userfont0 if j["Certificate"][0] == "U" else userfont,
            )
            if j["Certificate"] == "EES_Appreciation_Coordinator":
                draw.text(
                    xy=(980, 830),
                    text="{}".format(j["Designation"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
                draw.text(
                    xy=(1330, 655),
                    text="{}".format(j["Event"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
                draw.text(
                    xy=(700, 715),
                    text="{}".format(j["Category"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
            if (
                j["Certificate"] == "EES_Appreciation_Core"
                or j["Certificate"] == "EES_Appreciation_Core_2"
            ):
                draw.text(
                    xy=(970, 660),
                    text="{}".format(j["Designation"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
            if j["Certificate"] == "EES_Merit":
                draw.text(
                    xy=(985, 657),
                    text="{}".format(j["Event"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
                draw.text(
                    xy=(500, 725),
                    text="{}".format(j["Category"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
                draw.text(
                    xy=(950, 845),
                    text="{}".format(j["Position"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
            if j["Certificate"] == "EES_Participation":
                draw.text(
                    xy=(960, 670),
                    text="{}".format(j["Event"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
                draw.text(
                    xy=(500, 745),
                    text="{}".format(j["Category"]),
                    fill=(0, 0, 0),
                    font=userfont1,
                )
            if (
                j["Certificate"] == "Udyam_Appreciation"
                or j["Certificate"] == "Udyam_Appreciation_2"
            ):
                draw.text(
                    xy=(630, 550),
                    text="{}".format(j["Designation"]),
                    fill=(0, 0, 0),
                    font=userfont,
                )
            if j["Certificate"] == "Udyam_Merit":
                draw.text(
                    xy=(547, 432),
                    text="{}".format(j["Event"]),
                    fill=(0, 0, 0),
                    font=userfont,
                )
                draw.text(
                    xy=(647, 522),
                    text="{}".format(j["Position"]),
                    fill=(0, 0, 0),
                    font=userfont,
                )
            if j["Certificate"] == "Udyam_Participation":
                draw.text(
                    xy=(647, 435),
                    text="{}".format(j["Event"]),
                    fill=(0, 0, 0),
                    font=userfont,
                )
            if (
                j["Certificate"] == "EES_Merit"
                or j["Certificate"] == "EES_Participation"
                or j["Certificate"] == "Udyam_Merit"
                or j["Certificate"] == "Udyam_Participation"
            ):
                img.save(
                    "static/certificates/{}_{}_{}.png".format(
                        j["Event"], j["Serial Number"], index
                    )
                )
            else:
                img.save(
                    "static/certificates/{}_{}_{}.png".format(
                        j["Designation"], j["Serial Number"], index
                    )
                )

    shutil.make_archive("static/certificates", "zip", "static/certificates")
    zip_file = open("static/certificates.zip", "rb")
    return zip_file


class CertificateGetUserView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        print(request.user.email)
        zip_file = createCerti(request.user.email)
        response = HttpResponse(FileWrapper(zip_file), content_type="application/zip")
        response["Content-Disposition"] = (
             'attachment; filename="%s"' % "certificates.zip"
        )
        os.remove("static/certificates.zip")
        shutil.rmtree("static/certificates")
        return response
