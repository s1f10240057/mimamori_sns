from django.urls import path
from . import views

app_name = 'mypage'

urlpatterns = [
    path('', views.ProfileView.as_view(), name='profile'),
    path('password/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]
