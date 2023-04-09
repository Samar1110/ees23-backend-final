from django.urls import path
from .views import *  # TeamCreateView, ViewAllEvent,TeamCountView, GetAllNoticeView,TeamGetUserView

urlpatterns = [
    path("events/", ViewAllEvent.as_view(), name="get-all-events"),
    path("team/create/", TeamCreateView.as_view(), name="team-create"),
    path("team/count/", TeamCountView.as_view(), name="team-count"),
    path("updates/<str:event>", GetAllNoticeView.as_view(), name="notices"),
    path("teams/user/", TeamGetUserView.as_view(), name="teams-user"),
    path("team/<int:id>/", TeamView.as_view(), name="team"),
    path(
        "certificates/user", CertificateGetUserView.as_view(), name="certificates-user"
    ),
]
