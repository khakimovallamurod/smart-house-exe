from django.contrib import admin

from .models import House, RelatedPerson, Resident, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    fields = ("room_number", "family_status", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ("house_number", "street_name", "room_count", "created_at", "updated_at")
    search_fields = ("house_number", "street_name")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("house", "room_number", "family_status", "created_at", "updated_at")
    search_fields = ("house__house_number", "house__street_name", "room_number")
    list_filter = ("family_status", "created_at")
    ordering = ("house", "room_number")


class RelatedPersonInline(admin.TabularInline):
    model = RelatedPerson
    extra = 0


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ("fullname", "room", "relationship", "phone", "has_violation", "created_at")
    search_fields = ("fullname", "phone", "passport", "pinfl", "room__house__house_number")
    list_filter = ("relationship", "gender", "has_violation", "created_at")
    ordering = ("fullname",)
    inlines = [RelatedPersonInline]


@admin.register(RelatedPerson)
class RelatedPersonAdmin(admin.ModelAdmin):
    list_display = ("fullname", "resident", "relationship", "phone", "organization", "created_at")
    search_fields = ("fullname", "phone", "organization", "resident__fullname")
    list_filter = ("created_at", "organization")
    ordering = ("fullname",)

# Register your models here.
