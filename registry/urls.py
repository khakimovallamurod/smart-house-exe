from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = "registry"

urlpatterns = [
    path("", login_required(views.dashboard), name="dashboard"),
    path("houses/", login_required(views.house_list), name="house_list"),
    path("settings/", login_required(views.settings_page), name="settings"),
    path("settings/houses/<int:pk>/rooms/", login_required(views.settings_house_rooms), name="settings_house_rooms"),
    path("settings/rooms/<int:pk>/residents/", login_required(views.settings_room_residents), name="settings_room_residents"),
    path("settings/rooms/<int:room_pk>/residents/add/", login_required(views.resident_create), name="resident_create"),
    path("settings/residents/<int:pk>/edit/", login_required(views.resident_edit), name="resident_edit"),
    path("houses/<int:pk>/", login_required(views.house_detail), name="house_detail"),
    path("houses/<int:pk>/edit/", login_required(views.house_edit), name="house_edit"),
    path("houses/<int:pk>/delete/", login_required(views.house_delete), name="house_delete"),
    path("rooms/<int:pk>/modal/", login_required(views.room_modal), name="room_modal"),
    path("rooms/<int:pk>/info-modal/", login_required(views.apartment_info_modal), name="apartment_info_modal"),
    path("rooms/<int:pk>/residents/", login_required(views.room_residents_view), name="room_residents_view"),
    path("residents/<int:pk>/delete/", login_required(views.resident_delete), name="resident_delete"),
    path("api/stats/", login_required(views.stats_api), name="stats_api"),
]
