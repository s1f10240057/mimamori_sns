from django.contrib import admin
from django.urls import path
import mimamori.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('top', mimamori.views.root)
]
