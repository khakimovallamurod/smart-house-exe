from django.core.exceptions import ValidationError
from django.db import models, transaction


class House(models.Model):
    COLOR_CHOICES = [
        ("blue", "Ko'k"),
        ("green", "Yashil"),
        ("red", "Qizil"),
        ("amber", "Sariq"),
        ("slate", "Kulrang"),
    ]

    house_number = models.CharField(max_length=40)
    street_name = models.CharField(max_length=180)
    room_count = models.PositiveIntegerField()
    entrance_count = models.PositiveIntegerField(default=4)
    apartments_per_entrance = models.PositiveIntegerField(default=8)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="blue")
    entrance_camera = models.BooleanField(default=False)
    entrance_camera_count = models.PositiveIntegerField(blank=True, null=True)
    yard_camera = models.BooleanField(default=False)
    yard_camera_count = models.PositiveIntegerField(blank=True, null=True)
    entrance_sos_button = models.BooleanField(default=False)
    entrance_sos_button_count = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["house_number", "street_name"],
                name="unique_house_per_street",
            )
        ]

    def __str__(self):
        return f"{self.house_number}-uy, {self.street_name}"

    def clean(self):
        if self.entrance_count <= 0:
            raise ValidationError({"entrance_count": "Podyezd soni noldan katta bo'lishi kerak."})
        if self.apartments_per_entrance <= 0:
            raise ValidationError({"apartments_per_entrance": "Podyezddagi xonadon soni noldan katta bo'lishi kerak."})

    def save(self, *args, **kwargs):
        creating = self.pk is None
        old_count = None
        if not creating:
            old_count = House.objects.filter(pk=self.pk).values_list("room_count", flat=True).first()

        self.room_count = self.entrance_count * self.apartments_per_entrance
        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating:
                self.create_rooms()
            elif old_count is not None and self.room_count != old_count:
                self.sync_rooms(old_count)
            else:
                self.sync_room_entrances()

    def entrance_for_room(self, room_number):
        return ((room_number - 1) // self.apartments_per_entrance) + 1

    def create_rooms(self):
        Room.objects.bulk_create(
            [
                Room(
                    house=self,
                    room_number=number,
                    entrance_number=self.entrance_for_room(number),
                )
                for number in range(1, self.room_count + 1)
            ]
        )

    def sync_rooms(self, old_count):
        if self.room_count > old_count:
            Room.objects.bulk_create(
                [
                    Room(
                        house=self,
                        room_number=number,
                        entrance_number=self.entrance_for_room(number),
                    )
                    for number in range(old_count + 1, self.room_count + 1)
                ]
            )
        elif self.room_count < old_count:
            self.rooms.filter(room_number__gt=self.room_count, residents__isnull=True).delete()
            occupied_overflow = self.rooms.filter(room_number__gt=self.room_count).exists()
            if occupied_overflow:
                self.room_count = old_count
                super().save(update_fields=["room_count", "updated_at"])
                raise ValidationError("Ichida a'zolari bor xonalarni o'chirib bo'lmaydi.")
        self.sync_room_entrances()

    def sync_room_entrances(self):
        for room in self.rooms.all():
            expected = self.entrance_for_room(room.room_number)
            if room.entrance_number != expected:
                room.entrance_number = expected
                room.save(update_fields=["entrance_number", "updated_at"])

    @property
    def occupied_rooms_count(self):
        return self.rooms.filter(residents__isnull=False).distinct().count()

    @property
    def empty_rooms_count(self):
        return self.room_count - self.occupied_rooms_count


class Room(models.Model):
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"
    FAMILY_STATUS_CHOICES = [
        (LARGE, "Katta oila"),
        (MEDIUM, "O'rta oila"),
        (SMALL, "Kichik oila"),
    ]

    house = models.ForeignKey(House, related_name="rooms", on_delete=models.CASCADE)
    room_number = models.PositiveIntegerField()
    entrance_number = models.PositiveIntegerField(default=1)
    family_status = models.CharField(max_length=20, choices=FAMILY_STATUS_CHOICES, default=SMALL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room_number"]
        constraints = [
            models.UniqueConstraint(fields=["house", "room_number"], name="unique_room_per_house")
        ]

    def __str__(self):
        return f"{self.house} - {self.room_number}-xona"

    @property
    def is_occupied(self):
        return self.residents.exists()

    @property
    def has_violation(self):
        return self.residents.filter(has_violation=True).exists()


class Resident(models.Model):
    LIVING_STATUS_CHOICES = [
        ("owner", "Uy egasi"),
        ("tenant", "Ijarada yashovchi"),
        ("member", "A'zo"),
    ]
    RELATIONSHIP_CHOICES = [
        ("self", "O'zi"),
        ("son", "O'g'il"),
        ("daughter", "Qiz"),
        ("mother", "Ona"),
        ("brother", "Akasi"),
        ("sister", "Opasi"),
        ("friend", "Do'sti"),
        ("other", "Boshqa"),
    ]
    GENDER_CHOICES = [("male", "Erkak"), ("female", "Ayol"), ("other", "Boshqa")]
    SOCIAL_CONCLUSION_PROVIDER_CHOICES = [
        ("mayor_assistant", "Hokim yordamchisi"),
        ("women_activist", "Xotin-qizlar faoli"),
        ("prevention_inspector", "Profilaktika inspektori"),
        ("youth_leader", "Yoshlar yetakchisi"),
        ("social_protection", "Ijtimoiy himoya vakili"),
        ("tax_inspector", "Soliq inspektori"),
    ]

    room = models.ForeignKey(Room, related_name="residents", on_delete=models.CASCADE)
    photo = models.FileField(upload_to="residents/", blank=True, null=True)
    living_status = models.CharField(max_length=20, choices=LIVING_STATUS_CHOICES, default="owner")
    has_rental_contract = models.BooleanField(default=False)
    rental_contract_file = models.FileField(upload_to="resident_documents/", blank=True, null=True)
    has_temporary_registration = models.BooleanField(default=False)
    temporary_registration_file = models.FileField(upload_to="resident_documents/", blank=True, null=True)
    daily_rental_guest_home = models.BooleanField(default=False)
    has_origin_neighborhood_conclusion = models.BooleanField(default=False)
    origin_neighborhood_conclusion_note = models.TextField(blank=True)
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES, default="other")
    fullname = models.CharField(max_length=180)
    phone = models.CharField(max_length=40, blank=True)
    passport = models.CharField(max_length=40, blank=True)
    pinfl = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    is_working = models.BooleanField(default=False)
    occupation = models.CharField(max_length=120, blank=True)
    workplace = models.CharField(max_length=180, blank=True)
    is_studying = models.BooleanField(default=False)
    education = models.CharField(max_length=120, blank=True)
    has_violation = models.BooleanField(default=False)
    violation_description = models.TextField(blank=True)
    violation_date = models.DateField(blank=True, null=True)
    officer_name = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    long_abroad = models.BooleanField(default=False)
    abroad_country = models.CharField(max_length=120, blank=True)
    abroad_year = models.PositiveIntegerField(blank=True, null=True)
    abroad_duration = models.CharField(max_length=120, blank=True)
    abroad_reason = models.TextField(blank=True)
    previously_convicted = models.BooleanField(default=False)
    conviction_year = models.PositiveIntegerField(blank=True, null=True)
    conviction_article = models.CharField(max_length=80, blank=True)
    conviction_part = models.CharField(max_length=80, blank=True)
    conviction_note = models.TextField(blank=True)
    penal_institution = models.BooleanField(default=False)
    penal_institution_location = models.CharField(max_length=180, blank=True)
    penal_institution_note = models.TextField(blank=True)
    probation = models.BooleanField(default=False)
    probation_start_year = models.PositiveIntegerField(blank=True, null=True)
    probation_end_year = models.PositiveIntegerField(blank=True, null=True)
    probation_article = models.CharField(max_length=80, blank=True)
    probation_part = models.CharField(max_length=80, blank=True)
    probation_note = models.TextField(blank=True)
    administrative_supervision = models.BooleanField(default=False)
    administrative_supervision_start_year = models.PositiveIntegerField(blank=True, null=True)
    administrative_supervision_end_year = models.PositiveIntegerField(blank=True, null=True)
    preventive_register = models.BooleanField(default=False)
    preventive_register_start_year = models.PositiveIntegerField(blank=True, null=True)
    preventive_register_end_year = models.PositiveIntegerField(blank=True, null=True)
    preventive_register_date = models.DateField(blank=True, null=True)
    preventive_register_article = models.CharField(max_length=180, blank=True)
    preventive_register_part = models.CharField(max_length=80, blank=True)
    preventive_register_note = models.TextField(blank=True)
    deo_register = models.BooleanField(default=False)
    deo_start_year = models.PositiveIntegerField(blank=True, null=True)
    deo_end_year = models.PositiveIntegerField(blank=True, null=True)
    deo_article = models.CharField(max_length=80, blank=True)
    deo_part = models.CharField(max_length=80, blank=True)
    deo_note = models.TextField(blank=True)
    alcohol_addiction = models.BooleanField(default=False)
    alcohol_addiction_note = models.TextField(blank=True)
    troubled_family = models.BooleanField(default=False)
    troubled_family_note = models.TextField(blank=True)
    mental_health_register = models.BooleanField(default=False)
    disability_register = models.BooleanField(default=False)
    hunting_weapon = models.BooleanField(default=False)
    weapon_count = models.PositiveIntegerField(blank=True, null=True)
    weapon_model = models.CharField(max_length=180, blank=True)
    drug_addiction_register = models.BooleanField(default=False)
    drug_addiction_since = models.CharField(max_length=120, blank=True)
    needs_social_assistance = models.BooleanField(default=False)
    social_assistance_note = models.TextField(blank=True)
    security_panel_connected = models.BooleanField(default=False)
    has_complaints = models.BooleanField(default=False)
    complaint_count = models.PositiveIntegerField(blank=True, null=True)
    complaint_notes = models.JSONField(default=list, blank=True)
    social_conclusion = models.BooleanField(default=False)
    social_conclusion_provider = models.CharField(
        max_length=40,
        choices=SOCIAL_CONCLUSION_PROVIDER_CHOICES,
        blank=True,
    )
    social_conclusion_file = models.FileField(upload_to="resident_documents/", blank=True, null=True)
    social_conclusion_note = models.TextField(blank=True)
    joint_conclusion = models.BooleanField(default=False)
    joint_conclusion_file = models.FileField(upload_to="resident_documents/", blank=True, null=True)
    joint_conclusion_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fullname"]

    def __str__(self):
        return self.fullname


class RelatedPerson(models.Model):
    resident = models.ForeignKey(Resident, related_name="related_persons", on_delete=models.CASCADE)
    photo = models.FileField(upload_to="related_persons/", blank=True, null=True)
    fullname = models.CharField(max_length=180)
    relationship = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    organization = models.CharField(max_length=180, blank=True)
    membership = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fullname"]

    def __str__(self):
        return self.fullname

# Create your models here.
