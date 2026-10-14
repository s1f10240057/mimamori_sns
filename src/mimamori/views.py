from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import json
from accounts.models import User
from mimamori.models import Photo, Invitation, PairRelationship
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST
# Create your views here.

def root(request):
    return HttpResponse("Hello Django and Docker")

def index(request):
    return render(request, "mimamori/index.html", {})

def get_pairs(user):
    relations = (
        PairRelationship.objects
        .filter(Q(a_user=user) | Q(b_user=user))
        .select_related("a_user", "b_user")
    )
    return [
        r.b_user if r.a_user_id == user.id else r.a_user
        for r in relations
    ]

def timeline(request):
    context = {}
    pairs = get_pairs(request.user) if request.user.is_authenticated else []
    context["user_pair"] = pairs
    photos = Photo.objects.order_by("created_at")
    if request.GET.get('filter') == "pair":
         photos = photos.filter(posted_user__in=[u for u in pairs])
    context["photos"] = photos
    return render(request, "mimamori/timeline.html", context)

def postPhotoAPI(request):
    response_data = {"success" : False}
    if request.method == "POST":
        photo_data = request.FILES.get('photo')
        photo = Photo(
            image = photo_data,
            posted_user = request.user,
        )
        photo.save()
        response_data = {
                "success" : True,
            }
    return JsonResponse(response_data)

@require_POST
def getPairTokenAPI(request):
    try:
        invitation = Invitation.objects.create(
        inviter=request.user,
        expires_at=timezone.now() + timedelta(days=1),
        )
        link = request.build_absolute_uri(f"/mimamori/invite/{invitation.token}")
        response_data = {
            "success" : True,
            "link" : link
        }
    except:
        response_data = {"success" : False, "link": None}
    return JsonResponse(response_data)

@require_POST
def makePairAPI(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        inv = Invitation.objects.get(token = data.get('token'))
        PairRelationship.objects.get_or_create(
            a_user=inv.inviter,
            b_user=request.user,
        )
        response_data = {
            "success" : True
        }
    except Exception as e:
        print(e)
        response_data = {"success" : False}
    return JsonResponse(response_data)

def invite(request, token):
    context = {}
    invitation = Invitation.objects.get(token = token)
    context["inviter"] = invitation.inviter
    context["token"] = token
    return render(request, "mimamori/invite.html", context)

