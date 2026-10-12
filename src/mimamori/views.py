from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import json
from accounts.models import User
from mimamori.models import Photo
# Create your views here.

def root(request):
    return HttpResponse("Hello Django and Docker")

def index(request):
    return render(request, "mimamori/index.html", {})

def timeline(request):
    photo = Photo.objects.order_by("created_at")
    dict = {}
    dict["photos"] = photo
    return render(request, "mimamori/timeline.html", dict)

def postPhotoAPI(request):
    response_data = {"success" : False}
    if request.method == "POST":
        # data = json.loads(request.body.decode('utf-8'))
        photo_data = request.FILES.get('photo')
        who_id = -1
        photo = Photo(
            image = photo_data,
            who_id = who_id,
        )
        photo.save()
        response_data = {
                "success" : True,
            }
    return JsonResponse(response_data)
