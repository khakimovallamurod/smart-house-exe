from django import forms

from .models import House, Resident, Room


INPUT_CLASS = "form-input"
CHECK_CLASS = "h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
RADIO_CLASS = "h-4 w-4 border-slate-300 text-blue-600 focus:ring-blue-500"
BOOLEAN_CHOICES = ((False, "Yo'q"), (True, "Ha"))


class StyledModelForm(forms.ModelForm):
    placeholders = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": CHECK_CLASS})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({"class": "choice-list"})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({"class": "form-file"})
            else:
                field.widget.attrs.update({"class": INPUT_CLASS})
                placeholder = self.placeholders.get(field_name) or field.label
                field.widget.attrs.setdefault("placeholder", placeholder)


class HouseForm(StyledModelForm):
    placeholders = {
        "house_number": "Masalan: 15",
        "street_name": "Masalan: Yangi hayot",
        "entrance_count": "Masalan: 4",
        "apartments_per_entrance": "Masalan: 10",
        "entrance_camera_count": "Masalan: 4",
        "yard_camera_count": "Masalan: 4",
        "entrance_sos_button_count": "Masalan: 4",
    }

    class Meta:
        model = House
        fields = [
            "street_name",
            "house_number",
            "entrance_count",
            "apartments_per_entrance",
            "color",
            "entrance_camera",
            "entrance_camera_count",
            "yard_camera",
            "yard_camera_count",
            "entrance_sos_button",
            "entrance_sos_button_count",
        ]
        labels = {
            "street_name": "Mahalla nomi",
            "house_number": "Uy raqami",
            "entrance_count": "Podyezd soni",
            "apartments_per_entrance": "1 ta podyezddagi xonadon soni",
            "color": "Uy rangi",
            "entrance_camera": "Podyezd eshigi oldiga kamera qo'yilganmi?",
            "entrance_camera_count": "Podyezd eshigi oldidagi kameralar soni",
            "yard_camera": "Uy atrofi kameralashtirilganmi?",
            "yard_camera_count": "Uy atrofidagi kameralar soni",
            "entrance_sos_button": "Podyezdga SOS tugma qo'yilganmi?",
            "entrance_sos_button_count": "Podyezddagi SOS tugmalar soni",
        }
        widgets = {
            "entrance_count": forms.NumberInput(attrs={"min": 1}),
            "apartments_per_entrance": forms.NumberInput(attrs={"min": 1}),
            "entrance_camera": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "entrance_camera_count": forms.NumberInput(attrs={"min": 1}),
            "yard_camera": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "yard_camera_count": forms.NumberInput(attrs={"min": 1}),
            "entrance_sos_button": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "entrance_sos_button_count": forms.NumberInput(attrs={"min": 1}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("entrance_camera"):
            cleaned["entrance_camera_count"] = None
        if not cleaned.get("yard_camera"):
            cleaned["yard_camera_count"] = None
        if not cleaned.get("entrance_sos_button"):
            cleaned["entrance_sos_button_count"] = None
        return cleaned

    def clean_entrance_count(self):
        entrance_count = self.cleaned_data["entrance_count"]
        if entrance_count <= 0:
            raise forms.ValidationError("Podyezd soni noldan katta bo'lishi kerak.")
        return entrance_count

    def clean_apartments_per_entrance(self):
        apartments_per_entrance = self.cleaned_data["apartments_per_entrance"]
        if apartments_per_entrance <= 0:
            raise forms.ValidationError("Xonadon soni noldan katta bo'lishi kerak.")
        return apartments_per_entrance


class RoomStatusForm(StyledModelForm):
    class Meta:
        model = Room
        fields = ["family_status"]
        labels = {"family_status": "Oila holati"}


class ResidentBasicForm(StyledModelForm):
    placeholders = {
        "fullname": "Masalan: Ali Valiyev",
        "phone": "Masalan: +998 90 123 45 67",
        "birth_date": "Tug'ilgan sanani tanlang",
        "occupation": "Masalan: o'qituvchi",
        "violation_description": "Huquqbuzarlik bo'lsa qisqacha yozing",
        "notes": "Qo'shimcha izoh",
    }

    class Meta:
        model = Resident
        fields = [
            "relationship",
            "fullname",
            "phone",
            "birth_date",
            "gender",
            "occupation",
            "has_violation",
            "violation_description",
            "notes",
        ]
        labels = {
            "relationship": "Qarindoshlik",
            "fullname": "To'liq ism",
            "phone": "Telefon raqami",
            "birth_date": "Tug'ilgan sana",
            "gender": "Jinsi",
            "occupation": "Kasbi",
            "has_violation": "Huquqbuzarlik bormi?",
            "violation_description": "Huquqbuzarlik izohi",
            "notes": "Qo'shimcha izoh",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "violation_description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class ResidentOwnerForm(StyledModelForm):
    placeholders = {
        "fullname": "Masalan: Ali Valiyev",
        "phone": "+998 90 123 45 67",
        "pinfl": "14 xonali JSHSHIRni kiriting",
        "occupation": "Masalan: haydovchi",
        "workplace": "Masalan: Samarqand shahar IIB",
        "education": "Masalan: Samarqand davlat universiteti",
        "abroad_country": "Masalan: Rossiya",
        "abroad_year": "Masalan: 2024",
        "abroad_duration": "Masalan: 2 yil",
        "abroad_reason": "Nima sababdan chetga chiqqanini yozing",
        "conviction_year": "Masalan: 2020",
        "conviction_article": "Masalan: 169-modda",
        "conviction_part": "Masalan: 2-qism",
        "conviction_note": "Qisqacha izoh",
        "penal_institution_location": "Masalan: 3-son JIEM",
        "penal_institution_note": "Qayerdaligi yoki qo'shimcha izoh",
        "probation_start_year": "Boshlanish yili",
        "probation_end_year": "Tugash yili",
        "probation_article": "Masalan: 169-modda",
        "probation_part": "Masalan: 2-qism",
        "probation_note": "Probatsiya bo'yicha izoh",
        "administrative_supervision_start_year": "Boshlanish yili",
        "administrative_supervision_end_year": "Tugash yili",
        "preventive_register_article": "Masalan: tegishli modda",
        "preventive_register_start_year": "Boshlanish yili",
        "preventive_register_end_year": "Tugash yili",
        "preventive_register_part": "Masalan: 2-qism",
        "preventive_register_note": "Profilaktik hisob bo'yicha izoh",
        "deo_start_year": "Boshlanish yili",
        "deo_end_year": "Tugash yili",
        "deo_article": "Masalan: tegishli modda",
        "deo_part": "Masalan: qismi",
        "deo_note": "DEO ro'yxati bo'yicha izoh",
        "alcohol_addiction_note": "Spirtli ichimlik bo'yicha izoh",
        "troubled_family_note": "Kim bilan va nima sababdan notinchligini yozing",
        "weapon_count": "Masalan: 1",
        "weapon_model": "Masalan: IJ-27",
        "drug_addiction_since": "Masalan: 2021-yildan beri",
        "social_assistance_note": "Qanday yordamga muhtojligini yozing",
        "origin_neighborhood_conclusion_note": "Fuqaro to'g'risidagi ma'lumotni yozing",
        "wanted_person_note": "Qidiruvdagi shaxs bo'yicha izoh",
        "complaint_count": "Murojaatlar soni",
        "social_conclusion_provider": "Xulosa kim tomonidan berilgan?",
        "social_conclusion_note": "Ijtimoiy xulosa izohi",
        "joint_conclusion_note": "Qo'shma xulosa izohi",
        "notes": "Qo'shimcha izoh",
    }

    class Meta:
        model = Resident
        fields = [
            "living_status",
            "has_rental_contract",
            "rental_contract_file",
            "has_temporary_registration",
            "temporary_registration_file",
            "daily_rental_guest_home",
            "has_origin_neighborhood_conclusion",
            "origin_neighborhood_conclusion_note",
            "relationship",
            "photo",
            "fullname",
            "birth_date",
            "gender",
            "phone",
            "pinfl",
            "is_working",
            "occupation",
            "workplace",
            "is_studying",
            "education",
            "long_abroad",
            "abroad_country",
            "abroad_year",
            "abroad_duration",
            "abroad_reason",
            "previously_convicted",
            "conviction_year",
            "conviction_article",
            "conviction_part",
            "conviction_note",
            "penal_institution",
            "penal_institution_location",
            "penal_institution_note",
            "probation",
            "probation_start_year",
            "probation_end_year",
            "probation_article",
            "probation_part",
            "probation_note",
            "administrative_supervision",
            "administrative_supervision_start_year",
            "administrative_supervision_end_year",
            "preventive_register",
            "preventive_register_start_year",
            "preventive_register_end_year",
            "preventive_register_date",
            "preventive_register_article",
            "preventive_register_part",
            "preventive_register_note",
            "deo_register",
            "deo_start_year",
            "deo_end_year",
            "deo_article",
            "deo_part",
            "deo_note",
            "alcohol_addiction",
            "alcohol_addiction_note",
            "troubled_family",
            "troubled_family_note",
            "mental_health_register",
            "disability_register",
            "hunting_weapon",
            "weapon_count",
            "weapon_model",
            "drug_addiction_register",
            "drug_addiction_since",
            "needs_social_assistance",
            "social_assistance_note",
            "security_panel_connected",
            "cybersecurity_bot_connected",
            "wanted_person",
            "wanted_person_note",
            "has_complaints",
            "complaint_count",
            "social_conclusion",
            "social_conclusion_provider",
            "social_conclusion_file",
            "social_conclusion_note",
            "joint_conclusion",
            "joint_conclusion_file",
            "joint_conclusion_note",
            "notes",
        ]
        labels = {
            "living_status": "Yashash holati",
            "has_rental_contract": "Ijara shartnomasi bormi?",
            "rental_contract_file": "Ijara shartnomasi fayli",
            "has_temporary_registration": "Vaqtinchalik propiska bormi?",
            "temporary_registration_file": "Vaqtinchalik propiska fayli",
            "daily_rental_guest_home": "Ushbu xonadon kunlik ijaraga beriladigan mehmon xonadonmi?",
            "has_origin_neighborhood_conclusion": "Doimiy yashash joydagi mahalla proflaktika inspektoridan fuqaro to'g'risidagi ma'lumot",
            "origin_neighborhood_conclusion_note": "Doimiy yashash joydagi mahalla proflaktika inspektoridan fuqaro to'g'risidagi ma'lumot",
            "relationship": "Qarindoshlik",
            "photo": "Rasm",
            "fullname": "F.I.Sh",
            "birth_date": "Tug'ilgan sana",
            "gender": "Jinsi",
            "phone": "Telefon raqami",
            "pinfl": "Pasport JSHSHIR",
            "is_working": "Ushbu shaxs ishlaydimi?",
            "occupation": "Kasbi",
            "workplace": "Qayerda ishlaydi?",
            "is_studying": "Ushbu shaxs o'qiydimi?",
            "education": "Qayerda o'qiydi?",
            "long_abroad": "Ushbu shaxs uzoq muddatga chet davlatga chiqib ketganmi?",
            "abroad_country": "Qaysi davlat",
            "abroad_year": "Nechanchi yil",
            "abroad_duration": "Qancha muddatga",
            "abroad_reason": "Chetga chiqish sababi",
            "previously_convicted": "Ushbu shaxs muqaddam sudlanganmi?",
            "conviction_year": "Nechanchi yil",
            "conviction_article": "Modda",
            "conviction_part": "Qism",
            "conviction_note": "Izoh",
            "penal_institution": "Jazoni ijro etish muassasasi bilan bog'liq holati bormi?",
            "penal_institution_location": "Qayerdaligi",
            "penal_institution_note": "Izoh",
            "probation": "Ushbu shaxs probatsiya hisobida turadimi?",
            "probation_start_year": "Boshlanish yili",
            "probation_end_year": "Tugash yili",
            "probation_article": "Modda",
            "probation_part": "Qism",
            "probation_note": "Izoh",
            "administrative_supervision": "Ushbu shaxs ma'muriy nazoratda turadimi?",
            "administrative_supervision_start_year": "Boshlanish yili",
            "administrative_supervision_end_year": "Tugash yili",
            "preventive_register": "Ushbu shaxs profilaktik hisob ro'yxatida turadimi?",
            "preventive_register_start_year": "Boshlanish yili",
            "preventive_register_end_year": "Tugash yili",
            "preventive_register_date": "Qachondan beri",
            "preventive_register_article": "Qaysi modda",
            "preventive_register_part": "Qism",
            "preventive_register_note": "Izoh",
            "deo_register": "DEO ro'yxatida turadimi?",
            "deo_start_year": "Boshlanish yili",
            "deo_end_year": "Tugash yili",
            "deo_article": "Modda",
            "deo_part": "Qism",
            "deo_note": "Izoh",
            "alcohol_addiction": "Ushbu shaxs spirtli ichimliklarga ruju qo'yganmi?",
            "alcohol_addiction_note": "Izoh",
            "troubled_family": "Ushbu xonadon notinch oila hisoblanadimi?",
            "troubled_family_note": "Izoh",
            "mental_health_register": "Ushbu shaxs ruhiy kasallar ro'yxatida turadimi?",
            "disability_register": "Ushbu shaxs nogironlik ro'yxatida turadimi?",
            "hunting_weapon": "Ushbu shaxsda ov quroli bormi?",
            "weapon_count": "Qurol soni",
            "weapon_model": "Qurol markasi",
            "drug_addiction_register": "Ushbu shaxs giyohvandlik ro'yxatida turadimi?",
            "drug_addiction_since": "Qachondan beri",
            "needs_social_assistance": "Ushbu xonadon ijtimoiy yordamga muhtojmi?",
            "social_assistance_note": "Izoh",
            "security_panel_connected": "Xonadonga qo'riqlov pulti o'rnatilganmi?",
            "cybersecurity_bot_connected": "Kiberxavfsizlik bo'yicha botga ulanganmi?",
            "wanted_person": "Ushbu xonadonda qidiruvdagi shaxs bormi?",
            "wanted_person_note": "Izoh",
            "has_complaints": "Mazkur xonadondan murojaat tushganmi?",
            "complaint_count": "Murojaatlar soni",
            "social_conclusion": "Ijtimoiy xulosa berilganmi?",
            "social_conclusion_provider": "Ijtimoiy xulosa kim tomonidan berilgan?",
            "social_conclusion_file": "Ijtimoiy xulosa fayli",
            "social_conclusion_note": "Izoh",
            "joint_conclusion": "Qo'shma xulosa berilganmi?",
            "joint_conclusion_file": "Qo'shma xulosa fayli",
            "joint_conclusion_note": "Izoh",
            "notes": "Qo'shimcha izoh",
        }
        widgets = {
            "living_status": forms.RadioSelect,
            "has_rental_contract": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "has_temporary_registration": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "daily_rental_guest_home": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "has_origin_neighborhood_conclusion": forms.HiddenInput(),
            "pinfl": forms.TextInput(attrs={"maxlength": 14, "pattern": r"\d{14}", "inputmode": "numeric"}),
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "is_working": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "is_studying": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "long_abroad": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "previously_convicted": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "penal_institution": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "probation": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "administrative_supervision": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "preventive_register": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "preventive_register_date": forms.DateInput(attrs={"type": "date"}),
            "deo_register": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "alcohol_addiction": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "troubled_family": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "mental_health_register": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "disability_register": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "hunting_weapon": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "drug_addiction_register": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "needs_social_assistance": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "security_panel_connected": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "cybersecurity_bot_connected": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "wanted_person": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "has_complaints": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "social_conclusion": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "joint_conclusion": forms.RadioSelect(choices=BOOLEAN_CHOICES),
            "abroad_reason": forms.Textarea(attrs={"rows": 3}),
            "conviction_note": forms.Textarea(attrs={"rows": 3}),
            "penal_institution_note": forms.Textarea(attrs={"rows": 3}),
            "probation_note": forms.Textarea(attrs={"rows": 3}),
            "preventive_register_note": forms.Textarea(attrs={"rows": 3}),
            "deo_note": forms.Textarea(attrs={"rows": 3}),
            "alcohol_addiction_note": forms.Textarea(attrs={"rows": 3}),
            "troubled_family_note": forms.Textarea(attrs={"rows": 3}),
            "social_assistance_note": forms.Textarea(attrs={"rows": 3}),
            "social_conclusion_note": forms.Textarea(attrs={"rows": 3}),
            "joint_conclusion_note": forms.Textarea(attrs={"rows": 3}),
            "origin_neighborhood_conclusion_note": forms.Textarea(attrs={"rows": 3}),
            "wanted_person_note": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("living_status") != "tenant":
            cleaned["has_rental_contract"] = False
            cleaned["rental_contract_file"] = None
            cleaned["has_temporary_registration"] = False
            cleaned["temporary_registration_file"] = None
            cleaned["daily_rental_guest_home"] = False
            cleaned["has_origin_neighborhood_conclusion"] = False
            cleaned["origin_neighborhood_conclusion_note"] = ""
        if not cleaned.get("has_rental_contract"):
            cleaned["rental_contract_file"] = None
        if not cleaned.get("has_temporary_registration"):
            cleaned["temporary_registration_file"] = None
        cleaned["has_origin_neighborhood_conclusion"] = bool(cleaned.get("origin_neighborhood_conclusion_note", "").strip())
        if not cleaned.get("is_working"):
            cleaned["occupation"] = ""
            cleaned["workplace"] = ""
        if not cleaned.get("is_studying"):
            cleaned["education"] = ""
        if not cleaned.get("long_abroad"):
            cleaned["abroad_country"] = ""
            cleaned["abroad_year"] = None
            cleaned["abroad_duration"] = ""
            cleaned["abroad_reason"] = ""
        if not cleaned.get("previously_convicted"):
            cleaned["conviction_year"] = None
            cleaned["conviction_article"] = ""
            cleaned["conviction_part"] = ""
            cleaned["conviction_note"] = ""
        if not cleaned.get("penal_institution"):
            cleaned["penal_institution_location"] = ""
            cleaned["penal_institution_note"] = ""
        if not cleaned.get("probation"):
            cleaned["probation_start_year"] = None
            cleaned["probation_end_year"] = None
            cleaned["probation_article"] = ""
            cleaned["probation_part"] = ""
            cleaned["probation_note"] = ""
        if not cleaned.get("administrative_supervision"):
            cleaned["administrative_supervision_start_year"] = None
            cleaned["administrative_supervision_end_year"] = None
        if not cleaned.get("preventive_register"):
            cleaned["preventive_register_start_year"] = None
            cleaned["preventive_register_end_year"] = None
            cleaned["preventive_register_date"] = None
            cleaned["preventive_register_article"] = ""
            cleaned["preventive_register_part"] = ""
            cleaned["preventive_register_note"] = ""
        if not cleaned.get("deo_register"):
            cleaned["deo_start_year"] = None
            cleaned["deo_end_year"] = None
            cleaned["deo_article"] = ""
            cleaned["deo_part"] = ""
            cleaned["deo_note"] = ""
        if not cleaned.get("alcohol_addiction"):
            cleaned["alcohol_addiction_note"] = ""
        if not cleaned.get("troubled_family"):
            cleaned["troubled_family_note"] = ""
        if not cleaned.get("hunting_weapon"):
            cleaned["weapon_count"] = None
            cleaned["weapon_model"] = ""
        if not cleaned.get("drug_addiction_register"):
            cleaned["drug_addiction_since"] = ""
        if not cleaned.get("needs_social_assistance"):
            cleaned["social_assistance_note"] = ""
        if not cleaned.get("wanted_person"):
            cleaned["wanted_person_note"] = ""
        if not cleaned.get("has_complaints"):
            cleaned["complaint_count"] = None
        if not cleaned.get("social_conclusion"):
            cleaned["social_conclusion_provider"] = ""
            cleaned["social_conclusion_file"] = None
            cleaned["social_conclusion_note"] = ""
        if not cleaned.get("joint_conclusion"):
            cleaned["joint_conclusion_file"] = None
            cleaned["joint_conclusion_note"] = ""
        return cleaned

    def clean_pinfl(self):
        pinfl = self.cleaned_data.get("pinfl", "").strip()
        if pinfl and (not pinfl.isdigit() or len(pinfl) != 14):
            raise forms.ValidationError("JSHSHIR 14 ta raqamdan iborat bo'lishi kerak.")
        return pinfl
