from django.contrib import admin
from django.urls import path, include
from . import views



app_name = "mimamori"

urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('top', mimamori.views.root),
    # path('mimamori/', include('mimamori.urls')),
    path('index/', views.index, name = "index"),
    path('timeline/', views.timeline, name = "timeline"),
    path('postAPI/', views.postPhotoAPI, name = "photo"),
    path('getPairTokenAPI/', views.getPairTokenAPI, name = "getPairToken"),
    path('makePairAPI/', views.makePairAPI, name = "makePair"),
    path('invite/<str:token>', views.invite, name = "invite"),
]
