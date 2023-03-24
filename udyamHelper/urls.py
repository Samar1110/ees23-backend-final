from django.urls import path
from .views import* # TeamCreateView, ViewAllEvent,TeamCountView, GetAllNoticeView,TeamGetUserView

urlpatterns = [
    path("events/", ViewAllEvent.as_view(), name="get-all-events"),
    path("team/create/", TeamCreateView.as_view(), name="team-create"),
    path("team/count/", TeamCountView.as_view(), name="team-count"),
    path("updates/<str:event>", GetAllNoticeView.as_view(), name="notices"),
    path("teams/user/", TeamGetUserView.as_view(), name="teams-user"),
    path("export_users_xls", export_users_xls, name="export-users-xls"),
    path("export_teams_xls", export_teams_xls, name="export-teams-xls"),
    path("team/<int:id>/", TeamView.as_view(), name="team"),
]
