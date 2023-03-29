from rest_framework import serializers, generics, status
# from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserAcount
from rest_framework import permissions
import xlwt
import pandas as pd
import shutil
from django.http import HttpResponse
from django.http import Http404
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from typing import Tuple
from udyamBackend.settings import CLIENT_ID, CLIENT_SECRET
import requests
from django.core.mail import send_mail,EmailMultiAlternatives
from .models import BroadCast_Email
from django.shortcuts import render
from.models import BroadCast_Email
from.forms import PostForm
from django.http import HttpResponseRedirect
from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token
from decouple import config
from googleapiclient.discovery import build
from google.oauth2 import service_account
from udyamHelper.models import Team, Event
from django.core.validators import RegexValidator
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from .services import google_get_access_token, google_get_user_info
GOOGLE_ID_TOKEN_INFO_URL = 'https://oauth2.googleapis.com/tokeninfo'

def google_validate(*, code: str) -> bool:
    redirect_uri = "https://eesiitbhu.in"
    print(CLIENT_ID)
    print(CLIENT_SECRET)
    try:
        access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
    except:
        access_token=code
    user_data = google_get_user_info(access_token=access_token)
    user_data={
        "givenName":user_data["given_name"]+" "+user_data["family_name"],
        "email":user_data["email"],
        "code": access_token
    }
    return user_data


def user_create(email, **extra_field) -> UserAcount:
    extra_fields = {
        'is_staff': False,
        'is_active': True,
        **extra_field
    }

    print(extra_fields)

    user = UserAcount(email=email, **extra_fields)
    user.save()
    populate_googlesheet_with_user_data() 
    return user


def user_get_or_create(*, email: str, **extra_data) -> Tuple[UserAcount, bool]:
    user = UserAcount.objects.filter(email=email).first()

    if user:
        return user, False
    return user_create(email=email, **extra_data), True

def user_get_me(*, user: UserAcount):
    token,_ = Token.objects.get_or_create(user = user)
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'college': user.college_name,
        'year': user.year,
        'phone': user.phone_number,
        'radianite_points': user.radianite_points,
        'referral': user.email[:5]+"#EES-"+str(10000+user.id),
        'token': token.key,
        'message': "Your registration was successfull!",
    }

def user_referred(*, referral):
    if not referral: return
    [verify,id]=referral.split("#EES-")
    user=UserAcount.objects.filter(id=(int(id)-10000))
    if user.count()!=0 and user[0].email[:5]==verify:
        user.update(radianite_points=user[0].radianite_points+5)

class InputSerializer(serializers.Serializer):
        
        phone_message = 'Phone number must be entered in the format: 9XXXXXXXXX' 

        phone_regex = RegexValidator(
            regex=r'^[789]\d{9}$',
            message=phone_message
        )
        email = serializers.EmailField()
        name = serializers.CharField(required=True)
        college_name = serializers.CharField(required=True)
        year = serializers.CharField(required=True)
        phone_number = serializers.CharField(validators=[phone_regex], max_length=60, required=True)

class UserInitApi(generics.GenericAPIView):
    serializer_class=InputSerializer

    def post(self, request, *args, **kwargs):
        code = request.headers.get('Authorization')
        userData=google_validate(code=code)
        email=userData["email"]

        if UserAcount.objects.filter(email=email).count()==0:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid() or email!=request.data["email"]:
                error = {"data":userData}
                for err in serializer.errors:
                    error[err] = serializer.errors[err][0]
                return Response(error, status=status.HTTP_409_CONFLICT)
            user_get_or_create(**serializer.validated_data)
            user_referred(referral=request.data.get("referral"))

        response = Response(data=user_get_me(user=UserAcount.objects.get(email=email)))
        return response


class LogoutView(generics.GenericAPIView):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class =  InputSerializer

    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_200_OK)


class UpdateApi(generics.GenericAPIView):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InputSerializer
    def patch(self, request, id):
        try:
            user = UserAcount.objects.get(id=id)
            serializer = self.serializer_class(data = request.data)
            if not serializer.is_valid():
                error = {}
                for err in serializer.errors:
                    error[err] = serializer.errors[err][0]
                return Response(error, status=status.HTTP_409_CONFLICT)
                
            user.name = request.data['name']
            user.college_name = request.data['college_name']
            user.phone_number = request.data['phone_number']
            user.year = request.data['year']
            user.save()
            return Response(
                {"success": "User Account successfully updated"}, status=status.HTTP_200_OK
            )
        except UserAcount.DoesNotExist:
            return Response(
                {"error": "User account not found"}, status=status.HTTP_404_NOT_FOUND
            )

  

@api_view(('GET',))
def leaderBoard(request):
    users = UserAcount.objects.filter(radianite_points__gt=0).order_by("-radianite_points").values()
    array=[]
    for user in users :
        array.append({
            "name":user['name'],
            "email":user['email'],
            "radianite_points":user['radianite_points'],
            "phone_number":user['phone_number'],
        })
        if(len(array)==10):
            break
    return Response({"array":array}, status=status.HTTP_200_OK)



    
    
def broadcast_mail(request,subject,created):


    if request.method == "GET" and request.user.has_perm("view_broadcast_email"):
        message = BroadCast_Email.objects.get(subject=subject,created=created).message
        users = UserAcount.objects.all()
        list_email_user = [user.email for user in users]
        n = 100
        list_group = [
            list_email_user[i: i + n] for i in range(0, len(list_email_user), n)
        ]
        for group in list_group:
            email = EmailMessage(subject, message, bcc=group)
            email.content_subtype = "html"
            email.send()

        return HttpResponse("Mail sent successfully")
    return HttpResponse("Invalid request")


def index(request):

    subject = None
    created = None
    form = None
    if request.method == "POST" and request.user.has_perm("view_broadcast_email"):
        form = PostForm(request.POST)
        if form.is_valid():
            print(subject)
            form.save()
            subject=request.POST['subject']
            created=request.POST['created']
    elif request.user.has_perm("view_broadcast_email"):

        form = PostForm()

    else :
        return HttpResponse("Invalid request")

    return render(request, 'index.html',{'form':form,'subject':subject,'created':created})

def populate_googlesheet_with_user_data() :
    """Populate Googlesheet with the coin data from the database."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_id = config('SPREADSHEET_ID', default='1cLNkflUYzDkkHg02qF1oQ3ons-T41g8E4JRKEb4HCWE')
    service_account_file = 'excelsheet-381920-4c0c0a0a6e7a.json'
    creds = None
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()


    user_queryset = UserAcount.objects.all().order_by('id')
    data: list[any] = []


    for user in user_queryset:
        data.append(
            [
                user.name,
                user.email,
                user.year,
                user.college_name,
                user.radianite_points,
            ]
        )

    sheet.values().clear(spreadsheetId=spreadsheet_id, range='A2:F').execute()
    sheet.values().append(
        spreadsheetId=spreadsheet_id, range='USERDATA!A2:F2', valueInputOption='USER_ENTERED', body={'values': data}
    ).execute()
    
def populate_googlesheet_with_team_data() :
    """Populate Googlesheet with the coin data from the database."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_id = config('SPREADSHEET_ID', default='1cLNkflUYzDkkHg02qF1oQ3ons-T41g8E4JRKEb4HCWE')
    service_account_file = 'excelsheet-381920-4c0c0a0a6e7a.json'
    creds = None
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()


    team_queryset = Team.objects.order_by("-event")
    data: list[any] = []


    for team in team_queryset:
        data.append(
            [
                team.event.event,
                team.teamname,
                team.leader.name, 
                team.leader.email, 
                team.leader.phone_number, 
                team.member1.name if(team.member1) else " ", 
                team.member1.email if(team.member1) else " ", 
                team.member1.phone_number if(team.member1) else " ", 
                team.member2.name if(team.member2) else " ", 
                team.member2.email if(team.member2) else " ", 
                team.member2.phone_number if(team.member2) else " ",
            ]
        )

    sheet.values().clear(spreadsheetId=spreadsheet_id, range='A2:K').execute()
    sheet.values().append(
        spreadsheetId=spreadsheet_id, range='TEAMDATA!A2:K2', valueInputOption='USER_ENTERED', body={'values': data}
    ).execute()
    
def populate_googlesheet_with_collegteam_data() :
    """Populate Googlesheet with the coin data from the database."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_id = config('SPREADSHEET_ID', default='1cLNkflUYzDkkHg02qF1oQ3ons-T41g8E4JRKEb4HCWE')
    service_account_file = 'excelsheet-381920-4c0c0a0a6e7a.json'
    creds = None
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    data: list[any] = []
    college_team = {}
    teamObj=Team.objects.all()
    for x in teamObj:
        print(x)
        if(x.leader.college_name in college_team.keys()):
            college_team[x.leader.college_name]+=1
        else:
            college_team[x.leader.college_name]=1
    
    for x in college_team.keys():
        print(x)
        data.append([x,college_team[x]])

    sheet.values().clear(spreadsheetId=spreadsheet_id, range='A2:B').execute()
    sheet.values().append(
        spreadsheetId=spreadsheet_id, range='COLLEGETEAMCOUNT!A2:B2', valueInputOption='USER_ENTERED', body={'values': data}
    ).execute()
    
def populate_googlesheet_with_eventTeam_data() :
    """Populate Googlesheet with the coin data from the database."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_id = config('SPREADSHEET_ID', default='1cLNkflUYzDkkHg02qF1oQ3ons-T41g8E4JRKEb4HCWE')
    service_account_file = 'excelsheet-381920-4c0c0a0a6e7a.json'
    creds = None
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    data: list[any] = []
    for event in Event.objects.all():
        data.append([event.event,Team.objects.filter(event=event).count()])
        
    sheet.values().clear(spreadsheetId=spreadsheet_id, range='A2:B').execute()
    sheet.values().append(
        spreadsheetId=spreadsheet_id, range='EVENT-TEAMCOUNT!A2:B2', valueInputOption='USER_ENTERED', body={'values': data}
    ).execute()