import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import HouseForm, ResidentBasicForm, ResidentOwnerForm, RoomStatusForm
from .models import House, RelatedPerson, Resident, Room


def dashboard(request):
    houses = House.objects.all()
    rooms = Room.objects.select_related("house")
    residents = Resident.objects.select_related("room", "room__house")
    occupied_rooms = rooms.filter(residents__isnull=False).distinct()

    stats = {
        "total_houses": houses.count(),
        "total_rooms": rooms.count(),
        "occupied_rooms": occupied_rooms.count(),
        "empty_rooms": rooms.count() - occupied_rooms.count(),
        "large_families": rooms.filter(family_status=Room.LARGE).count(),
        "medium_families": rooms.filter(family_status=Room.MEDIUM).count(),
        "small_families": rooms.filter(family_status=Room.SMALL).count(),
        "total_residents": residents.count(),
        "total_related_persons": RelatedPerson.objects.count(),
        "residents_with_violations": residents.filter(has_violation=True).count(),
    }
    context = {
        "page_title": "Boshqaruv paneli",
        "stats": stats,
        "recent_houses": houses.order_by("-created_at")[:5],
        "latest_rooms": rooms.order_by("-updated_at")[:6],
        "recent_residents": residents.order_by("-created_at")[:6],
        "status_summary": [
            ("Jami uylar", stats["total_houses"], "blue"),
            ("Band xonadonlar", stats["occupied_rooms"], "green"),
            ("Bo'sh xonadonlar", stats["empty_rooms"], "red"),
            ("Jami a'zolar", stats["total_residents"], "blue"),
        ],
    }
    return render(request, "registry/dashboard.html", context)


def house_list(request):
    houses = House.objects.annotate(
        occupied_rooms=Count("rooms", filter=Q(rooms__residents__isnull=False), distinct=True),
    ).order_by("-created_at")
    paginator = Paginator(houses, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "registry/house_list.html",
        {"page_title": "Asosiy sahifa", "page_obj": page_obj},
    )


def settings_page(request):
    houses = House.objects.annotate(
        occupied_rooms=Count("rooms", filter=Q(rooms__residents__isnull=False), distinct=True),
        residents_total=Count("rooms__residents", distinct=True),
    )
    if request.method == "POST":
        form = HouseForm(request.POST)
        if form.is_valid():
            house = form.save()
            messages.success(request, f"{house.house_number}-uy {house.room_count} ta xona bilan yaratildi.")
            return redirect("registry:settings")
        messages.error(request, "Belgilangan maydonlarni to'g'rilang.")
    else:
        form = HouseForm()
    return render(request, "registry/settings_manage.html", {"page_title": "Sozlash", "form": form, "houses": houses})


def settings_house_rooms(request, pk):
    house = get_object_or_404(House, pk=pk)
    rooms = house.rooms.annotate(
        resident_count=Count("residents", distinct=True),
        violation_count=Count("residents", filter=Q(residents__has_violation=True), distinct=True),
    )
    return render(
        request,
        "registry/settings_rooms.html",
        {"page_title": f"{house.house_number}-uy xonalari", "house": house, "rooms": rooms},
    )


def settings_room_residents(request, pk):
    room = get_object_or_404(Room.objects.select_related("house"), pk=pk)
    residents = room.residents.all()
    supervision_fields = [
        "has_violation",
        "long_abroad",
        "previously_convicted",
        "penal_institution",
        "probation",
        "administrative_supervision",
        "preventive_register",
        "alcohol_addiction",
        "troubled_family",
        "mental_health_register",
        "disability_register",
        "hunting_weapon",
        "drug_addiction_register",
        "needs_social_assistance",
        "has_complaints",
        "social_conclusion",
    ]
    for resident in residents:
        resident.supervision_count = sum(1 for field in supervision_fields if getattr(resident, field))
    return render(
        request,
        "registry/settings_residents.html",
        {
            "page_title": f"{room.room_number}-xona a'zolari",
            "room": room,
            "residents": residents,
        },
    )


def resident_create(request, room_pk):
    room = get_object_or_404(Room.objects.select_related("house"), pk=room_pk)
    form = ResidentOwnerForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        resident = form.save(commit=False)
        resident.room = room
        resident.complaint_notes = [note for note in request.POST.getlist("complaint_notes") if note.strip()]
        resident.save()
        messages.success(request, "A'zo ma'lumotlari qo'shildi.")
        return redirect("registry:settings_room_residents", pk=room.pk)
    return render(
        request,
        "registry/resident_form.html",
        {"page_title": "A'zo qo'shish", "room": room, "form": form, "resident": None, "complaint_notes_json": "[]"},
    )


def resident_edit(request, pk):
    resident = get_object_or_404(Resident.objects.select_related("room", "room__house"), pk=pk)
    form = ResidentOwnerForm(request.POST or None, request.FILES or None, instance=resident)
    if request.method == "POST" and form.is_valid():
        resident = form.save(commit=False)
        resident.complaint_notes = [note for note in request.POST.getlist("complaint_notes") if note.strip()]
        resident.save()
        messages.success(request, "A'zo ma'lumotlari yangilandi.")
        return redirect("registry:settings_room_residents", pk=resident.room.pk)
    return render(
        request,
        "registry/resident_form.html",
        {
            "page_title": "A'zoni tahrirlash",
            "room": resident.room,
            "form": form,
            "resident": resident,
            "complaint_notes_json": json.dumps(resident.complaint_notes or []),
        },
    )


def room_residents_view(request, pk):
    room = get_object_or_404(Room.objects.select_related("house"), pk=pk)
    return render(
        request,
        "registry/room_residents_view.html",
        {"page_title": f"{room.room_number}-xona", "room": room, "residents": room.residents.all()},
    )


def apartment_info_modal(request, pk):
    room = get_object_or_404(Room.objects.select_related("house"), pk=pk)
    residents = list(
        room.residents.all().order_by(
            "living_status",
            "fullname",
        )
    )
    residents.sort(key=lambda item: {"owner": 0, "tenant": 1, "member": 2}.get(item.living_status, 3))
    return render(
        request,
        "registry/partials/apartment_info_modal.html",
        {"room": room, "residents": residents},
    )


def house_detail(request, pk):
    house = get_object_or_404(House, pk=pk)
    query = request.GET.get("q", "").strip()
    filter_value = request.GET.get("filter", "all")
    rooms = house.rooms.annotate(
        resident_count=Count("residents", distinct=True),
        violation_count=Count("residents", filter=Q(residents__has_violation=True), distinct=True),
    )
    if query:
        rooms = rooms.filter(
            Q(room_number__icontains=query)
            | Q(residents__fullname__icontains=query)
            | Q(residents__phone__icontains=query)
        ).distinct()
    if filter_value == "occupied":
        rooms = rooms.filter(residents__isnull=False).distinct()
    elif filter_value == "empty":
        rooms = rooms.filter(residents__isnull=True)
    elif filter_value in [Room.LARGE, Room.MEDIUM, Room.SMALL]:
        rooms = rooms.filter(family_status=filter_value)

    occupied = house.rooms.filter(residents__isnull=False).distinct().count()
    entrance_blocks = []
    for entrance_number in range(1, house.entrance_count + 1):
        entrance_rooms = list(rooms.filter(entrance_number=entrance_number))
        entrance_blocks.append({"number": entrance_number, "rooms": entrance_rooms})
    context = {
        "page_title": f"{house.house_number}-uy",
        "house": house,
        "rooms": rooms,
        "entrance_blocks": entrance_blocks,
        "query": query,
        "filter_value": filter_value,
        "occupied": occupied,
        "empty": house.room_count - occupied,
        "family_stats": {
            "large": house.rooms.filter(family_status=Room.LARGE).count(),
            "medium": house.rooms.filter(family_status=Room.MEDIUM).count(),
            "small": house.rooms.filter(family_status=Room.SMALL).count(),
        },
    }
    return render(request, "registry/house_detail.html", context)


def house_edit(request, pk):
    house = get_object_or_404(House, pk=pk)
    form = HouseForm(request.POST or None, instance=house)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Uy ma'lumotlari muvaffaqiyatli yangilandi.")
        return redirect("registry:house_list")
    return render(request, "registry/settings.html", {"page_title": "Uyni tahrirlash", "form": form, "house": house})


@require_POST
def house_delete(request, pk):
    house = get_object_or_404(House, pk=pk)
    house.delete()
    messages.success(request, "Uy muvaffaqiyatli o'chirildi.")
    return redirect("registry:settings")


def room_modal(request, pk):
    room = get_object_or_404(Room.objects.select_related("house"), pk=pk)
    residents = room.residents.all()
    status_form = RoomStatusForm(request.POST or None, instance=room, prefix="room")
    edit_resident = None
    edit_id = request.GET.get("edit_resident") or request.POST.get("edit_resident")
    if edit_id:
        edit_resident = get_object_or_404(Resident, pk=edit_id, room=room)
    resident_form = ResidentBasicForm(
        request.POST if request.POST.get("action") == "resident" else None,
        instance=edit_resident,
        prefix="resident",
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "status" and status_form.is_valid():
            status_form.save()
            messages.success(request, f"{room.room_number}-xona holati saqlandi.")
            return redirect("registry:house_detail", pk=room.house.pk)
        if action == "resident" and resident_form.is_valid():
            if status_form.is_valid():
                status_form.save()
            resident = resident_form.save(commit=False)
            resident.room = room
            resident.save()
            messages.success(request, f"{room.room_number}-xona ma'lumotlari saqlandi.")
            return redirect("registry:house_detail", pk=room.house.pk)
        messages.error(request, "Xona ma'lumotlarini to'g'rilang.")

    context = {
        "room": room,
        "residents": residents,
        "status_form": status_form,
        "resident_form": resident_form,
        "edit_resident": edit_resident,
        "post_url": reverse("registry:room_modal", args=[room.pk]),
    }
    return render(request, "registry/partials/room_modal.html", context)


@require_POST
def resident_delete(request, pk):
    resident = get_object_or_404(Resident.objects.select_related("room", "room__house"), pk=pk)
    room_pk = resident.room.pk
    house_pk = resident.room.house.pk
    resident.delete()
    messages.success(request, "A'zo o'chirildi.")
    if request.GET.get("next") == "settings":
        return redirect("registry:settings_room_residents", pk=room_pk)
    return redirect("registry:house_detail", pk=house_pk)


def stats_api(request):
    total_rooms = Room.objects.count()
    occupied = Room.objects.filter(residents__isnull=False).distinct().count()
    empty = max(total_rooms - occupied, 0)
    residents = Resident.objects.count()
    houses = House.objects.order_by("created_at")
    line = list(houses.values_list("room_count", flat=True)[:12])
    if len(line) == 1:
        line = [0, line[0]]
    return JsonResponse({
        "pie": [occupied, empty],
        "bar": [House.objects.count(), occupied, empty, residents],
        "bar_labels": ["Uy", "Band", "Bo'sh", "A'zo"],
        "line": line,
    })

# Create your views here.
