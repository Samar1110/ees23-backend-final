from django.urls import path
from .views import UserInitApi,broadcast_mail,index, LogoutView,leaderBoard, UpdateApi
from .admin import BroadCast_Email_Admin
urlpatterns = [
    path('google-login/', UserInitApi.as_view(), name='google-login'),
    path('user-update/<int:id>/', UpdateApi.as_view(), name='user-update'),
    path("broadcast/<subject>/<created>/", broadcast_mail, name="broadcast_mail"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("broadcaster", index),
    path("leaderboard",leaderBoard),
]
