from rest_framework import serializers, generics, status
# from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserAcount
from rest_framework import permissions
# from django.conf import settings
# from django.http import HttpResponse
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
        user.update(radianite_points=user[0].radianite_points+20)

class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        name = serializers.CharField(required=True)
        college_name = serializers.CharField(required=True)
        year = serializers.CharField(required=True)
        phone_number = serializers.CharField(required=True)

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
            print(user)
            print("hi")
            user.name = request.data['name']
            user.college_name = request.data['college_name']
            user.phone_number = request.data['phone_number']
            user.year = request.data['year']
            user.save() ;
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
            # return HttpResponseRedirect('/thanks/')
    elif request.user.has_perm("view_broadcast_email"):

        form = PostForm()

    else :
        return HttpResponse("Invalid request")

    return render(request, 'index.html',{'form':form,'subject':subject,'created':created})
