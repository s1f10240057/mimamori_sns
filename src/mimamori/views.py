from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
import json
from accounts.models import User
from mimamori.models import Photo, Invitation, PairRelationship
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Max

from notifications.models import NotificationSetting
# Create your views here.


def _open_task_qs(user):
    """自分宛てで、未提出・未スキップ・有効なタスク"""
    return NotificationSetting.objects.filter(
        receive_user=user,
        task_ended__isnull=True,
        skipped_at__isnull=True,
        # enabled=True,
    )

def _get_my_open_task(user, task_id):
    return _open_task_qs(user).filter(id=task_id).first()


def root(request):
    return HttpResponse("Hello Django and Docker")

def index(request):
    if request.user.is_authenticated and request.user.role == "A":
        return redirect("mimamori:timeline")
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



@login_required
def timeline(request):
    pairs = get_pairs(request.user)
    pair_ids = [u.id for u in pairs]

    if request.user.role == "A":
        photos = (
            Photo.objects
            .filter(posted_user_id__in=pair_ids)
            .select_related("posted_user", "task")
            .order_by("-created_at")
        )
    else:
        photos = (
            Photo.objects
            .select_related("posted_user", "task")
            .order_by("-created_at")
        )

    last_map = dict(
        Photo.objects
        .filter(posted_user_id__in=pair_ids)
        .values("posted_user_id")
        .annotate(last=Max("created_at"))
        .values_list("posted_user_id", "last")
    )
    last_posts = sorted(
        [{"user": u, "last": last_map.get(u.id)} for u in pairs],
        key=lambda x: (x["last"] is None, -(x["last"].timestamp() if x["last"] else 0)),
    )

    return render(request, "mimamori/timeline.html", {
        "photos": photos,
        "last_posts": last_posts,
        "is_watcher": request.user.role == "A",
        # "task_theme" は削除
    })

# def postPhotoAPI(request):
#     response_data = {"success" : False}
#     if request.method == "POST":
#         photo_data = request.FILES.get('photo')
#         task_id = request.POST.get('task_id')
#         photo = Photo(
#             image = photo_data,
#             posted_user = request.user,
#         )
#         photo.save()

#         if task_id != None:
#             noti = NotificationSetting.objects.get(id = int(task_id))
#             noti.task_ended = photo
#             noti.save()

#         response_data = {
#                 "success" : True,
#         }
#     return JsonResponse(response_data)

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


# def doTask(request, taskId):
#     return render(request, "mimamori/task.html", {"task_id": taskId})

@login_required
def pair(request):
    relations = (
        PairRelationship.objects
        .filter(Q(a_user=request.user) | Q(b_user=request.user))
        .select_related("a_user", "b_user")
        .order_by("-created_at")
    )
    pairs = [
        {
            "user": r.b_user if r.a_user_id == request.user.id else r.a_user,
            "created_at": r.created_at,
        }
        for r in relations
    ]
    return render(request, "mimamori/pair.html", {
        "pairs": pairs,
        "is_watcher": request.user.role == "A",
    })

def _get_my_open_task(user, task_id):
    """自分宛てで、未送信・有効なタスクだけ返す。なければ None"""
    return NotificationSetting.objects.filter(
        id=task_id,
        receive_user=user,
        task_ended__isnull=True,
        # enabled=True,
    ).first()


from django.http import Http404

@login_required
def doTask(request, taskId):
    task = _get_my_open_task(request.user, taskId)
    if task is None:
        n = NotificationSetting.objects.filter(id=taskId).first()
        print("DEBUG doTask:", {
            "login_user": request.user.id,
            "exists": n is not None,
            "receive_user": n.receive_user_id if n else None,
            "enabled": n.enabled if n else None,
            "task_ended": n.task_ended_id if n else None,
            "skipped_at": n.skipped_at if n else None,
        })
    return render(request, "mimamori/task.html", {
        "task_id": task.id if task else "",
        "task_available": task is not None,
        "task_theme": task.task_theme if task else "",
    })

@login_required
@require_POST
def postPhotoAPI(request):
    photo_data = request.FILES.get('photo')
    task_id = request.POST.get('task_id')
    skip = request.POST.get('skip') == "true"

    if photo_data is None and not skip:
        return JsonResponse({"success": False, "error": "no_photo"}, status=400)

    if not task_id:
        if skip:
            return JsonResponse({"success": False, "error": "bad_task"}, status=400)
        Photo.objects.create(image=photo_data, posted_user=request.user)
        return JsonResponse({"success": True})

    try:
        task_id = int(task_id)
    except ValueError:
        return JsonResponse({"success": False, "error": "bad_task"}, status=400)


    with transaction.atomic():
        noti = (
            _open_task_qs(request.user)
            .select_for_update()
            .filter(id=task_id)
            .first()
        )
        if noti is None:
            return JsonResponse({"success": False, "error": "unavailable"}, status=404)

        if skip:
            noti.skipped_at = timezone.now()
            noti.save(update_fields=["skipped_at"])
        else:
            photo =Photo.objects.create(image=photo_data, posted_user=request.user,
                                          task=NotificationSetting.objects.get(id=task_id))
            noti.task_ended = photo
            noti.save(update_fields=["task_ended"])

    return JsonResponse({"success": True})