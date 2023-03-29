from django.urls import path
from .views import UserInitApi,broadcast_mail,index, LogoutView,leaderBoard,populate_googlesheet_with_user_data
from .admin import BroadCast_Email_Admin
urlpatterns = [
    path('google-login/', UserInitApi.as_view(), name='google-login'),
    path("broadcast/<subject>/<created>/", broadcast_mail, name="broadcast_mail"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("broadcaster", index),
    path("leaderboard",leaderBoard),
    path("excelsheet",populate_googlesheet_with_user_data)
]
