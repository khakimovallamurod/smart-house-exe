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


HIGH_RISK_Q = (
    Q(previously_convicted=True)
    | Q(penal_institution=True)
    | Q(probation=True)
    | Q(administrative_supervision=True)
    | Q(preventive_register=True)
    | Q(deo_register=True)
)
MEDIUM_RISK_Q = (
    Q(alcohol_addiction=True)
    | Q(troubled_family=True)
    | Q(drug_addiction_register=True)
    | Q(has_complaints=True)
    | Q(cybersecurity_bot_connected=True)
)
ATTENTION_Q = HIGH_RISK_Q | MEDIUM_RISK_Q
SERIOUS_CRIME_Q = ATTENTION_Q
HIGH_RISK_ROOM_Q = (
    Q(residents__previously_convicted=True)
    | Q(residents__penal_institution=True)
    | Q(residents__probation=True)
    | Q(residents__administrative_supervision=True)
    | Q(residents__preventive_register=True)
    | Q(residents__deo_register=True)
)
MEDIUM_RISK_ROOM_Q = (
    Q(residents__alcohol_addiction=True)
    | Q(residents__troubled_family=True)
    | Q(residents__drug_addiction_register=True)
    | Q(residents__has_complaints=True)
    | Q(residents__cybersecurity_bot_connected=True)
)
SERIOUS_ROOM_Q = (
    Q(residents__previously_convicted=True)
    | Q(residents__penal_institution=True)
    | Q(residents__probation=True)
    | Q(residents__administrative_supervision=True)
    | Q(residents__preventive_register=True)
    | Q(residents__deo_register=True)
    | Q(residents__alcohol_addiction=True)
    | Q(residents__troubled_family=True)
    | Q(residents__drug_addiction_register=True)
    | Q(residents__has_complaints=True)
    | Q(residents__cybersecurity_bot_connected=True)
)
SERIOUS_HOUSE_Q = (
    Q(rooms__residents__previously_convicted=True)
    | Q(rooms__residents__penal_institution=True)
    | Q(rooms__residents__probation=True)
    | Q(rooms__residents__administrative_supervision=True)
    | Q(rooms__residents__preventive_register=True)
    | Q(rooms__residents__deo_register=True)
    | Q(rooms__residents__alcohol_addiction=True)
    | Q(rooms__residents__troubled_family=True)
    | Q(rooms__residents__drug_addiction_register=True)
    | Q(rooms__residents__has_complaints=True)
    | Q(rooms__residents__cybersecurity_bot_connected=True)
)

RISK_FACTOR_FIELDS = [
    "previously_convicted",
    "penal_institution",
    "probation",
    "administrative_supervision",
    "preventive_register",
    "deo_register",
    "alcohol_addiction",
    "troubled_family",
    "drug_addiction_register",
    "has_complaints",
    "cybersecurity_bot_connected",
]

RISK_METRICS = [
    ("previously_convicted", "Muqaddam sudlanganlar", "red", "resident"),
    ("penal_institution", "Jazoni ijro etish muassasasi bilan bog'liq holatlar", "red", "resident"),
    ("probation", "Probatsiya hisobida turuvchilar", "red", "resident"),
    ("administrative_supervision", "Ma'muriy nazoratda turuvchilar", "red", "resident"),
    ("preventive_register", "Profilaktik hisob ro'yxatida turuvchilar", "red", "resident"),
    ("deo_register", "DEO ro'yxatida turuvchilar", "red", "resident"),
    ("alcohol_addiction", "Spirtli ichimliklarga ruju qo'yganlar", "yellow", "resident"),
    ("troubled_family", "Notinch oila sifatida qayd etilgan xonadonlar", "yellow", "room"),
    ("drug_addiction_register", "Giyohvandlik ro'yxatida turuvchilar", "yellow", "resident"),
    ("has_complaints", "Murojaat tushgan xonadonlar", "yellow", "room"),
    ("cybersecurity_bot_connected", "Kiberxavfsizlik botiga ulanganlar", "yellow", "resident"),
]


def resident_risk_factor_count(resident):
    return sum(1 for field in RISK_FACTOR_FIELDS if getattr(resident, field))


def room_risk_factor_count(room):
    return sum(resident_risk_factor_count(resident) for resident in room.residents.all())


def risk_metric_cards(residents):
    cards = []
    for field, label, color, count_type in RISK_METRICS:
        matching = residents.filter(**{field: True})
        count = matching.values("room_id").distinct().count() if count_type == "room" else matching.count()
        cards.append({"key": field, "label": label, "color": color, "count": count})
    return cards


def resident_risk_labels(resident):
    return [label for field, label, _color, _count_type in RISK_METRICS if getattr(resident, field)]


def resident_card_payload(resident):
    risks = resident_risk_labels(resident)
    return {
        "id": resident.pk,
        "name": resident.fullname,
        "phone": resident.phone,
        "living_status": resident.get_living_status_display(),
        "relationship": resident.get_relationship_display(),
        "house_number": resident.room.house.house_number,
        "street_name": resident.room.house.street_name,
        "room_number": resident.room.room_number,
        "entrance_number": resident.room.entrance_number,
        "risk_count": len(risks),
        "risks": risks,
        "modal_url": reverse("registry:apartment_info_modal", args=[resident.room.pk]),
    }


def risk_people_groups(residents):
    groups = {}
    for field, label, color, _count_type in RISK_METRICS:
        people = residents.filter(**{field: True}).select_related("room", "room__house").order_by(
            "room__house__house_number",
            "room__entrance_number",
            "room__room_number",
            "fullname",
        )
        groups[field] = {
            "label": label,
            "color": color,
            "people": [resident_card_payload(resident) for resident in people],
        }
    return groups


def room_risk_summary_groups(rooms):
    groups = {
        "red": {"label": "Yuqori xavfli xonadonlar", "color": "red", "rooms": []},
        "yellow": {"label": "E'tibor talab qiladigan xonadonlar", "color": "yellow", "rooms": []},
        "green": {"label": "Barqaror xonadonlar", "color": "green", "rooms": []},
    }
    for room in rooms:
        if not room.resident_count:
            continue
        item = {
            "room_number": room.room_number,
            "entrance_number": room.entrance_number,
            "resident_count": room.resident_count,
            "risk_factor_count": room.risk_factor_count,
            "modal_url": reverse("registry:apartment_info_modal", args=[room.pk]),
        }
        if room.risk_factor_count >= 4:
            groups["red"]["rooms"].append(item)
        elif room.risk_factor_count > 0:
            groups["yellow"]["rooms"].append(item)
        else:
            groups["green"]["rooms"].append(item)
    return groups


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
        "serious_attention": residents.filter(SERIOUS_CRIME_Q).distinct().count(),
        "penal_institution_count": residents.filter(penal_institution=True).count(),
        "social_assistance_count": residents.filter(needs_social_assistance=True).count(),
    }
    context = {
        "page_title": "Boshqaruv paneli",
        "stats": stats,
        "risk_cards": risk_metric_cards(residents),
        "risk_people_groups": risk_people_groups(residents),
        "recent_houses": houses.order_by("-created_at")[:5],
        "latest_rooms": rooms.order_by("-updated_at")[:6],
        "recent_residents": residents.order_by("-created_at")[:6],
        "status_summary": [
            ("Jami uylar", stats["total_houses"], "blue"),
            ("Band xonadonlar", stats["occupied_rooms"], "green"),
            ("Bo'sh xonadonlar", stats["empty_rooms"], "red"),
            ("Jami fuqarolar", stats["total_residents"], "blue"),
            ("Og'ir nazorat", stats["serious_attention"], "red"),
            ("Ijtimoiy yordam", stats["social_assistance_count"], "blue"),
        ],
    }
    return render(request, "registry/dashboard.html", context)


def house_list(request):
    houses = House.objects.annotate(
        occupied_rooms=Count("rooms", filter=Q(rooms__residents__isnull=False), distinct=True),
        serious_attention=Count("rooms__residents", filter=SERIOUS_HOUSE_Q, distinct=True),
        penal_institution_count=Count("rooms__residents", filter=Q(rooms__residents__penal_institution=True), distinct=True),
        social_assistance_count=Count("rooms__residents", filter=Q(rooms__residents__needs_social_assistance=True), distinct=True),
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
            "page_title": f"{room.room_number}-xona fuqarolari",
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
        messages.success(request, "Fuqaro ma'lumotlari qo'shildi.")
        return redirect("registry:settings_room_residents", pk=room.pk)
    return render(
        request,
        "registry/resident_form.html",
        {"page_title": "Fuqaro qo'shish", "room": room, "form": form, "resident": None, "complaint_notes_json": "[]"},
    )


def resident_edit(request, pk):
    resident = get_object_or_404(Resident.objects.select_related("room", "room__house"), pk=pk)
    form = ResidentOwnerForm(request.POST or None, request.FILES or None, instance=resident)
    if request.method == "POST" and form.is_valid():
        resident = form.save(commit=False)
        resident.complaint_notes = [note for note in request.POST.getlist("complaint_notes") if note.strip()]
        resident.save()
        messages.success(request, "Fuqaro ma'lumotlari yangilandi.")
        return redirect("registry:settings_room_residents", pk=resident.room.pk)
    return render(
        request,
        "registry/resident_form.html",
        {
            "page_title": "Fuqaroni tahrirlash",
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
        serious_count=Count("residents", filter=SERIOUS_ROOM_Q, distinct=True),
        high_risk_count=Count("residents", filter=HIGH_RISK_ROOM_Q, distinct=True),
        medium_risk_count=Count("residents", filter=MEDIUM_RISK_ROOM_Q, distinct=True),
    ).prefetch_related("residents")
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

    house_residents = Resident.objects.filter(room__house=house)
    entrance_blocks = []
    entrance_risk_values = []
    all_house_rooms = []
    for entrance_number in range(1, house.entrance_count + 1):
        entrance_rooms = list(rooms.filter(entrance_number=entrance_number))
        for room in entrance_rooms:
            room.risk_factor_count = room_risk_factor_count(room)
        all_house_rooms.extend(entrance_rooms)
        red_rooms = sum(1 for room in entrance_rooms if room.risk_factor_count >= 4)
        yellow_rooms = sum(1 for room in entrance_rooms if 0 < room.risk_factor_count < 4)
        green_rooms = sum(1 for room in entrance_rooms if room.resident_count and room.risk_factor_count == 0)
        serious_count = house_residents.filter(room__entrance_number=entrance_number).filter(ATTENTION_Q).distinct().count()
        high_count = house_residents.filter(room__entrance_number=entrance_number).filter(HIGH_RISK_Q).distinct().count()
        medium_count = house_residents.filter(room__entrance_number=entrance_number).filter(MEDIUM_RISK_Q).distinct().count()
        penal_count = house_residents.filter(room__entrance_number=entrance_number, penal_institution=True).count()
        social_count = house_residents.filter(room__entrance_number=entrance_number, needs_social_assistance=True).count()
        entrance_risk_values.append(serious_count)
        entrance_blocks.append({
            "number": entrance_number,
            "rooms": entrance_rooms,
            "serious_count": serious_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "red_rooms": red_rooms,
            "yellow_rooms": yellow_rooms,
            "green_rooms": green_rooms,
            "penal_count": penal_count,
            "social_count": social_count,
        })
    max_entrance = max(entrance_blocks, key=lambda item: item["serious_count"], default=None)
    resident_search_items = []
    for resident in house_residents.select_related("room").order_by("fullname"):
        resident_search_items.append(resident_card_payload(resident))

    context = {
        "page_title": f"{house.house_number}-uy",
        "house": house,
        "rooms": rooms,
        "entrance_blocks": entrance_blocks,
        "query": query,
        "filter_value": filter_value,
        "serious_attention": house_residents.filter(ATTENTION_Q).distinct().count(),
        "high_risk_attention": house_residents.filter(HIGH_RISK_Q).distinct().count(),
        "medium_risk_attention": house_residents.filter(MEDIUM_RISK_Q).distinct().count(),
        "risk_cards": risk_metric_cards(house_residents),
        "risk_people_groups": risk_people_groups(house_residents),
        "room_risk_groups": room_risk_summary_groups(all_house_rooms),
        "resident_search_items": resident_search_items,
        "social_assistance_count": house_residents.filter(needs_social_assistance=True).count(),
        "max_entrance": max_entrance,
        "entrance_risk_json": json.dumps(entrance_risk_values),
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
    messages.success(request, "Fuqaro o'chirildi.")
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
        "pie_labels": ["Band", "Bo'sh"],
        "bar": [House.objects.count(), occupied, empty, residents],
        "bar_labels": ["Uy", "Band", "Bo'sh", "Fuqaro"],
        "line": line,
    })

# Create your views here.
