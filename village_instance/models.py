from django.db import models
from django.contrib.auth.models import User



# setup logo path to save logos
from urllib.parse import urlparse
from os.path import splitext, basename
def get_logo_path(instance, filename):
    disassembled = urlparse(filename)
    _, file_ext = splitext(basename(disassembled.path))
    return "logo_"+str(instance.url)+file_ext

# Create your models here.
# A Model to briefly describe each form
# It has enough information to contain all form related
# informations that will be on the admin page
class Forms(models.Model):
    CATEGORY = (
    ('Signalement', 'Signalement'),
    ('Etat Civil','Etat Civil'),
    ('Divers', 'Divers'),
    )
    name_id = models.CharField(max_length=200, null = True)
    name_descrip = models.CharField(max_length=200, null = True)
    category = models.CharField(max_length=200, null = True, choices=CATEGORY)
    description = models.CharField(max_length=200, blank=True, default=" ")
    url = models.CharField(max_length=200, null = True)
    def __str__(self):
        return str(self.name_id) + ' : ' + str(self.name_descrip) + ', ' + str(self.description)

# City is our user Extended Class
class City(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank = False)
    url = models.CharField(max_length=200, blank = False, unique = True)
    postal_code = models.CharField(max_length=200, blank = False)
    profile_image = models.ImageField(upload_to=get_logo_path, blank=True, null=True)
    forms = models.ManyToManyField(Forms, blank=True)
    COLORS = (
    ('Red', 'Rouge'),
    ('Blue','Bleu'),
    ('Green', 'Vert'),
    )
    color = models.CharField(max_length=200, blank=True, default='Red', choices=COLORS)
    def __str__(self):
        return self.name

from django.contrib import admin

class formsInline(admin.TabularInline):
    model = City.forms.through

class FormsAdmin(admin.ModelAdmin):
    inlines = [
        formsInline,
    ]

class CityAdmin(admin.ModelAdmin):
    inlines = [
        formsInline,
    ]
    exclude = ('forms',)
