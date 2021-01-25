from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import City, Forms
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

import re #regex

class UserMailOnly(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('email',)
    def save(self,commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# User creation form (reduced to relevant fields)
class ReducedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('username','email','password1', 'password2')
        labels = {
        "password1": _("Mot de passe"),
        "password2": _("Mot de passe 2"),
    }
    def save(self,commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# City (extended user) creation Form
class CityModifForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ('name', 'url', 'postal_code', 'profile_image','color')
        labels = {
        "name": _("Nom de votre commune"),
        "url": _("Adresse de la page citoyen de votre commune"),
        "postal_code": _("Code Postal"),
        "profile_image": _("Logo"),
    }
        error_messages = {
            'url': {
                'unique': """Une autre commune utilise déjà l'url que vous avez renseigné.
                        Merci de bien vouloir utiliser un autre url pour votre commune.""",
            }
        }
    def clean_url(self):
        data = self.cleaned_data['url']
        if re.search("^[\w\-]+$", data) is None :
            raise ValidationError("""Url non valide.
            Ce champ ne doit comporter que des chiffres, des lettres sans accent, - et _ """)
        return data

class CityRegisterForm(CityModifForm):
    exclude = ('color',)

# All possible forms that can be sent to a city
# https://stackoverflow.com/questions/17159567/how-to-create-a-list-of-fields-in-django-forms
# change settings without validation : https://stackoverflow.com/questions/55671266/how-to-use-toggle-switch-with-django-boolean-field
class ActivationCheckboxes(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super(ActivationCheckboxes, self).__init__(*args, **kwargs)
        counter = 1
        for q in questions:
            self.fields['question' + str(counter)] = forms.BooleanField(label=str(q.name_id),required=False)
            counter += 1

    def reformat_checkboxes(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('question'):
                yield (self.fields[name].label, value)

# A dropdown with all cities to simplify the choice for the user.
# To improve but fine at the moment
class CityDropDownForm(forms.Form):
    city = forms.ModelChoiceField(City.objects.all().order_by('name'), empty_label=None)
    def __init__(self, *args, **kwargs):
        super(CityDropDownForm, self).__init__(*args, **kwargs)
        self.fields['city'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        return '%s (%s)' % (obj.name, obj.postal_code)







##########################################################################
# From here, detail of each form that can be send by citizen to the cities.
##########################################################################
MAX_UPLOAD_SIZE = "5242880" #5M to ensure the full mail will be below 10M
class SignalementForm(forms.Form):
    nom = forms.CharField()
    prenom = forms.CharField()
    email = forms.CharField()
    phone = forms.CharField(required=False)
    street_number = forms.CharField(required=False)
    street = forms.CharField()
    city = forms.CharField()
    lat = forms.CharField(required=False)
    lng = forms.CharField(required=False)
    description = forms.CharField()
    pic1 = forms.ImageField(required=False)
    pic2 = forms.ImageField(required=False)
    def clean_pic1(self):
        pic = self.cleaned_data['pic1']
        if pic:
            if pic.size > 5242880: #5M to ensure the full mail will be below 10M
                raise forms.ValidationError(_("Merci de n'envoyer que des fichiers inférieurs à 5Mb. Taille du fichier courant : %s") % (filesizeformat(content._size)))
        return pic
    def clean_pic2(self):
        pic = self.cleaned_data['pic2']
        if pic:
            if pic.size > 5242880: #5M to ensure the full mail will be below 10M
                raise forms.ValidationError(_("Merci de n'envoyer que des fichiers inférieurs à 5Mb. Taille du fichier courant : %s") % (filesizeformat(content._size)))
        return pic

    def genEmailTitle(self, whichSignal):
        return "Signalement, " + whichSignal

    def genEmailContent(self, whichSignal):
        id_demandeur = self.cleaned_data['nom'].upper() + " "
        id_demandeur += self.cleaned_data['prenom'].capitalize()
        addressSignal = self.cleaned_data['street_number'] + " "
        addressSignal += self.cleaned_data['street'] + ", "
        addressSignal += self.cleaned_data['city']
        latlngLink = 'http://www.openstreetmap.org/?mlat='
        latlngLink += self.cleaned_data['lat'] + '&mlon='
        latlngLink += self.cleaned_data['lng'] + '&zoom=16'
        latlngString = '   , coordonnées : [' + self.cleaned_data['lat'] + ', '
        latlngString += self.cleaned_data['lng'] + ']'

        mailContent = """
Signalement : """ + whichSignal + """, via la plateforme de démarche en ligne demarches-villages.fr \n \n
Signalé par :
    Identité : """ + id_demandeur + """
    Telephone : """ + self.cleaned_data['phone'] + """
    Mail : """ + self.cleaned_data['email'] + """

Détail du signalement :
    Type : """ + whichSignal + """
    Lieu : """ + addressSignal
        if self.cleaned_data['lat'] != '' and self.cleaned_data['lat'] != ''  :
            mailContent += latlngString + """
        Sur une carte : """ + latlngLink
        mailContent += """
    Description : """ + self.cleaned_data['description'] + """ \n
Si des fichiers ont été ajoutés au signalement, ceux-ci sont disponibles en pièces jointes.
Attention ! Les fichiers n'ont pas été vérifiés par la plateforme mais simplement transmis.
Une fois téléchargés, vérifiez leur nature avant de les ouvrir
et ne les éxécutez pas s'il s'agit de programmes !"""

        return mailContent

# arrivée sur la commune
class ArriveeForm(forms.Form):
    nom = forms.CharField()
    prenom = forms.CharField()
    adresse = forms.CharField(widget=forms.Textarea)
    phone = forms.CharField(required=False)
    mail = forms.CharField()
    arrival_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))

    def genEmailTitle(self):
        return "Notification d'arrivée dans la commune"
    def genEmailContent(self):
        id_arrivant = self.cleaned_data['nom'].upper() + " " + self.cleaned_data['prenom'].capitalize()
        mailContent = """
Notification d'arrivée dans la commune envoyée via la plateforme de démarche en ligne demarches-villages.fr \n \n
Identité du nouvel arrivant : """ + id_arrivant + """
Adresse : """ + self.cleaned_data['adresse'] + """
Telephone : """ + self.cleaned_data['phone'] + """
Mail: """ + self.cleaned_data['mail'] + """

Date d'arrivée prévue : """ + self.cleaned_data['arrival_date'].strftime("%d-%m-%Y")
        return mailContent;



TYPE_ACTE = (
    ('', '----'),
    ("Copie intégrale", "Copie intégrale"),
    ("Extrait avec filiation", "Extrait avec filiation"),
    ("Extrait sans filiation", "Extrait sans filiation"),
)

QUALITES_DEMANDEUR_BASE = (
    ('', '----'),
    ("Son conjoint ou sa conjointe", "Son conjoint ou sa conjointe"),
    ("Son père ou sa mère", "Son père ou sa mère"),
    ("Son fils ou sa fille", "Son fils ou sa fille"),
    ("Son représentant légal", "Son représentant légal"),
    ("Autorité judiciaire ou administration autorisée","Autorité judiciaire ou administration autorisée"),
)
LIST_QUALITES_DEMANDEUR = list(QUALITES_DEMANDEUR_BASE)
LIST_QUALITES_DEMANDEUR.append(("Autre", "Autre"))
QUALITES_DEMANDEUR_DECES = tuple(LIST_QUALITES_DEMANDEUR)
LIST_QUALITES_DEMANDEUR = list(QUALITES_DEMANDEUR_BASE)
LIST_QUALITES_DEMANDEUR.insert(1, ("Personne concernée par l'acte",
    "Personne concernée par l'acte"))
QUALITES_DEMANDEUR_MARIAGE = tuple(LIST_QUALITES_DEMANDEUR)
LIST_QUALITES_DEMANDEUR.append(("Autre", "Autre"))
QUALITES_DEMANDEUR_NAISSANCE = tuple(LIST_QUALITES_DEMANDEUR)


class ActeNaissanceForm(forms.Form):
    demandeur_nom = forms.CharField()
    demandeur_prenom = forms.CharField()
    demandeur_adresse = forms.CharField(widget=forms.Textarea)
    demandeur_phone = forms.CharField()
    demandeur_mail = forms.CharField()
    demandeur_qualite = forms.ChoiceField(choices = QUALITES_DEMANDEUR_NAISSANCE)
    type_acte = forms.ChoiceField(choices = TYPE_ACTE)
    nombre_exemplaires = forms.IntegerField()
    person_acte_nom = forms.CharField()
    person_acte_prenom = forms.CharField()
    person_acte_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    person_acte_birthplace = forms.CharField()
    parent1_nom = forms.CharField()
    parent1_prenom = forms.CharField()
    parent1_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    parent1_birthplace = forms.CharField()
    parent2_nom = forms.CharField()
    parent2_prenom = forms.CharField()
    parent2_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    parent2_birthplace = forms.CharField()

    def genEmailTitle(self):
        return "Demande d'acte de naissance"

    def genEmailContent(self):
        id_demandeur = self.cleaned_data['demandeur_nom'].upper() + " "
        id_demandeur += self.cleaned_data['demandeur_prenom'].capitalize()

        id_person_acte = self.cleaned_data['person_acte_nom'].upper()
        id_person_acte += " " + self.cleaned_data['person_acte_prenom'].capitalize()

        id_parent1 = self.cleaned_data['parent1_nom'].upper()
        id_parent1 += " " + self.cleaned_data['parent1_prenom'].capitalize()
        id_parent1 += " né.e le " + self.cleaned_data['parent1_birthdate'].strftime("%d-%m-%Y")
        id_parent1 += " à " + self.cleaned_data['parent1_birthplace'].capitalize()

        id_parent2 = self.cleaned_data['parent2_nom'].upper()
        id_parent2 += " " + self.cleaned_data['parent2_prenom'].capitalize()
        id_parent2 += " né.e le " + self.cleaned_data['parent2_birthdate'].strftime("%d-%m-%Y")
        id_parent2 += " à " + self.cleaned_data['parent2_birthplace'].capitalize()


        mailContent = """
Demande d'acte de naissance envoyée via la plateforme de démarche en ligne demarches-villages.fr \n \n
Le demandeur :
    Identité : """ + id_demandeur + """
    Qualité vis à vis de la personne concernée par l'acte: """ + self.cleaned_data['demandeur_qualite'] + """
    Adresse : """ + self.cleaned_data['demandeur_adresse'] + """
    Telephone : """ + self.cleaned_data['demandeur_phone'] + """
    Mail : """ + self.cleaned_data['demandeur_mail'] + """

Type d'acte demandé : """ + self.cleaned_data['type_acte'] + """
Nombre d'actes demandés : """ + str(self.cleaned_data['nombre_exemplaires']) + """

Détails sur la naissance :
    Date : """ + self.cleaned_data['person_acte_birthdate'].strftime("%d-%m-%Y") + """
    Lieu : """ + self.cleaned_data['person_acte_birthplace'].capitalize() + """
    Nom du nouveau né : """ + id_person_acte + """
    Parents :
        """ + id_parent1 + """
        """ + id_parent2

        return mailContent;


class ActeMariageForm(forms.Form):
    demandeur_nom = forms.CharField()
    demandeur_prenom = forms.CharField()
    demandeur_adresse = forms.CharField(widget=forms.Textarea)
    demandeur_phone = forms.CharField()
    demandeur_mail = forms.CharField()
    demandeur_qualite = forms.ChoiceField(choices = QUALITES_DEMANDEUR_MARIAGE)
    type_acte = forms.ChoiceField(choices = TYPE_ACTE)
    nombre_exemplaires = forms.IntegerField()
    wedding_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint1_nom = forms.CharField()
    conjoint1_prenom = forms.CharField()
    conjoint1_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint1_birthplace = forms.CharField()
    conjoint1_parent1_nom = forms.CharField()
    conjoint1_parent1_prenom = forms.CharField()
    conjoint1_parent1_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint1_parent1_birthplace = forms.CharField()
    conjoint1_parent2_nom = forms.CharField()
    conjoint1_parent2_prenom = forms.CharField()
    conjoint1_parent2_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint1_parent2_birthplace = forms.CharField()
    conjoint2_nom = forms.CharField()
    conjoint2_prenom = forms.CharField()
    conjoint2_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint2_birthplace = forms.CharField()
    conjoint2_parent1_nom = forms.CharField()
    conjoint2_parent1_prenom = forms.CharField()
    conjoint2_parent1_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint2_parent1_birthplace = forms.CharField()
    conjoint2_parent2_nom = forms.CharField()
    conjoint2_parent2_prenom = forms.CharField()
    conjoint2_parent2_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    conjoint2_parent2_birthplace = forms.CharField()

    def genEmailTitle(self):
        return "Demande d'acte de mariage"

    def genEmailContent(self):
        id_demandeur = self.cleaned_data['demandeur_nom'].upper() + " "
        id_demandeur += self.cleaned_data['demandeur_prenom'].capitalize()

        id_conjoint1 = self.cleaned_data['conjoint1_nom'].upper()
        id_conjoint1 += " " + self.cleaned_data['conjoint1_prenom'].capitalize()
        id_conjoint1 += " né.e le " + self.cleaned_data['conjoint1_birthdate'].strftime("%d-%m-%Y")
        id_conjoint1 += " à " + self.cleaned_data['conjoint1_birthplace'].capitalize()

        id_conjoint1_parent1 = self.cleaned_data['conjoint1_parent1_nom'].upper()
        id_conjoint1_parent1 += " " + self.cleaned_data['conjoint1_parent1_prenom'].capitalize()
        id_conjoint1_parent1 += " né.e le " + self.cleaned_data['conjoint1_parent1_birthdate'].strftime("%d-%m-%Y")
        id_conjoint1_parent1 += " à " + self.cleaned_data['conjoint1_parent1_birthplace'].capitalize()
        id_conjoint1_parent2 = self.cleaned_data['conjoint1_parent2_nom'].upper()
        id_conjoint1_parent2 += " " + self.cleaned_data['conjoint1_parent2_prenom'].capitalize()
        id_conjoint1_parent2 += " né.e le " + self.cleaned_data['conjoint1_parent2_birthdate'].strftime("%d-%m-%Y")
        id_conjoint1_parent2 += " à " + self.cleaned_data['conjoint1_parent2_birthplace'].capitalize()

        id_conjoint2 = self.cleaned_data['conjoint2_nom'].upper()
        id_conjoint2 += " " + self.cleaned_data['conjoint2_prenom'].capitalize()
        id_conjoint2 += " né.e le " + self.cleaned_data['conjoint2_birthdate'].strftime("%d-%m-%Y")
        id_conjoint2 += " à " + self.cleaned_data['conjoint2_birthplace'].capitalize()

        id_conjoint2_parent1 = self.cleaned_data['conjoint2_parent1_nom'].upper()
        id_conjoint2_parent1 += " " + self.cleaned_data['conjoint2_parent1_prenom'].capitalize()
        id_conjoint2_parent1 += " né.e le " + self.cleaned_data['conjoint2_parent1_birthdate'].strftime("%d-%m-%Y")
        id_conjoint2_parent1 += " à " + self.cleaned_data['conjoint2_parent1_birthplace'].capitalize()
        id_conjoint2_parent2 = self.cleaned_data['conjoint2_parent2_nom'].upper()
        id_conjoint2_parent2 += " " + self.cleaned_data['conjoint2_parent2_prenom'].capitalize()
        id_conjoint2_parent2 += " né.e le " + self.cleaned_data['conjoint2_parent2_birthdate'].strftime("%d-%m-%Y")
        id_conjoint2_parent2 += " à " + self.cleaned_data['conjoint2_parent2_birthplace'].capitalize()


        mailContent = """
Demande d'acte de mariage envoyée via la plateforme de démarche en ligne demarches-villages.fr \n \n
Le demandeur :
    Identité : """ + id_demandeur + """
    Qualité vis à vis de la personne concernée par l'acte : """ + self.cleaned_data['demandeur_qualite'] + """
    Adresse : """ + self.cleaned_data['demandeur_adresse'] + """
    Telephone : """ + self.cleaned_data['demandeur_phone'] + """
    Mail : """ + self.cleaned_data['demandeur_mail'] + """

Type d'acte demandé : """ + self.cleaned_data['type_acte'] + """
Nombre d'actes demandés : """ + str(self.cleaned_data['nombre_exemplaires']) + """

Détails du mariage :
    Date : """ + self.cleaned_data['wedding_date'].strftime("%d-%m-%Y") + """
    Conjoints :
        """ + id_conjoint1 + """
                    fils/fille de :
                        """ + id_conjoint1_parent1 + """
                        """ + id_conjoint1_parent2 + """
        """ + id_conjoint2 + """
                    fils/fille de :
                        """ + id_conjoint2_parent1 + """
                        """ + id_conjoint2_parent2

        return mailContent;



class ActeDecesForm(forms.Form):
    demandeur_nom = forms.CharField()
    demandeur_prenom = forms.CharField()
    demandeur_adresse = forms.CharField(widget=forms.Textarea)
    demandeur_phone = forms.CharField()
    demandeur_mail = forms.CharField()
    demandeur_qualite = forms.ChoiceField(choices = QUALITES_DEMANDEUR_NAISSANCE)
    demandeur_qualite_autre = forms.CharField(required=False)
    nombre_exemplaires = forms.IntegerField()
    person_acte_nom = forms.CharField()
    person_acte_prenom = forms.CharField()
    person_acte_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    person_acte_birthplace = forms.CharField()
    person_acte_deathdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    parent1_nom = forms.CharField()
    parent1_prenom = forms.CharField()
    parent1_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    parent1_birthplace = forms.CharField()
    parent2_nom = forms.CharField()
    parent2_prenom = forms.CharField()
    parent2_birthdate = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
                    input_formats=('%d/%m/%Y', ))
    parent2_birthplace = forms.CharField()

    def genEmailTitle(self):
        return "Demande d'acte de décès"

    def genEmailContent(self):
        id_demandeur = self.cleaned_data['demandeur_nom'].upper() + " " + self.cleaned_data['demandeur_prenom'].capitalize()
        id_person_acte = self.cleaned_data['person_acte_nom'].upper() + " " + self.cleaned_data['person_acte_prenom'].capitalize()
        id_parent1 = self.cleaned_data['parent1_nom'].upper()
        id_parent1 += " " + self.cleaned_data['parent1_prenom'].capitalize()
        id_parent1 += " né.e le " + self.cleaned_data['parent1_birthdate'].strftime("%d-%m-%Y")
        id_parent1 += " à " + self.cleaned_data['parent1_birthplace'].capitalize()
        id_parent2 = self.cleaned_data['parent2_nom'].upper()
        id_parent2 += " " + self.cleaned_data['parent2_prenom'].capitalize()
        id_parent2 += " né.e le " + self.cleaned_data['parent2_birthdate'].strftime("%d-%m-%Y")
        id_parent2 += " à " + self.cleaned_data['parent2_birthplace'].capitalize()

        mailContent = """
Demande d'acte de décès envoyée via la plateforme de démarche en ligne demarches-villages.fr \n \n
Le demandeur :
    Identité : """ + id_demandeur + """
    Qualité vis à vis de la personne concernée par l'acte : """ + self.cleaned_data['demandeur_qualite']
        if self.cleaned_data['demandeur_qualite'] == "Autre" :
            mailContent += " : " +  self.cleaned_data['demandeur_qualite_autre']
        mailContent += """
    Adresse : """ + self.cleaned_data['demandeur_adresse'] + """
    Telephone : """ + self.cleaned_data['demandeur_phone'] + """
    Mail : """ + self.cleaned_data['demandeur_mail'] + """

Nombre d'actes demandés : """ + str(self.cleaned_data['nombre_exemplaires']) + """

Personne concernée par l'acte :
    Identité : """ + id_person_acte + """
    Date et lieu de naissance : """ + self.cleaned_data['person_acte_birthdate'].strftime("%d-%m-%Y") + ", " + self.cleaned_data['person_acte_birthplace'] + """
    Date de décès : """ + self.cleaned_data['person_acte_deathdate'].strftime("%d-%m-%Y") + """
    Ses parents :
        """ + id_parent1 + """
        """ + id_parent2

        return mailContent;

class AjoutSMSForm(forms.Form):
    nom = forms.CharField()
    prenom = forms.CharField()
    adresse = forms.CharField(widget=forms.Textarea)
    phone = forms.CharField()
    delay_inscription = forms.BooleanField(required=False)
    mail = forms.CharField(required=False)

    def genEmailTitle(self):
        return "Demande d'ajout sur les listes SMS"
    def genEmailContent(self):
        id_demandeur = self.cleaned_data['nom'].upper() + " " + self.cleaned_data['prenom'].capitalize()
        mailContent = """
Demande d'ajout sur les listes SMS envoyée via la plateforme de démarche en ligne demarches-villages.fr \n \n
Identité du demandeur : """ + id_demandeur + """
Adresse : """ + self.cleaned_data['adresse'] + """
Telephone : """ + self.cleaned_data['phone'] + """
Mail: """ + self.cleaned_data['mail'] + "\n"
        if self.cleaned_data['delay_inscription']:
            mailContent += """
Le demandeur souhaite d'abord recevoir des informations sur les SMS
qu'il est suceptible de recevoir  avant d'être inscrit aux différents services SMS.\n"""
        return mailContent;


SITUATION_INSCR_LIST_ELEC = (
    ('', '----'),
    ("Première inscription", "Première inscription"),
    ("Inscription suite à déménagement", "Inscription suite à déménagement"),
    ("Inscription pour un autre motif", "Inscription pour un autre motif"),
)

class AjoutListeElectoraleForm(forms.Form):
    nom = forms.CharField()
    prenoms = forms.CharField()
    adresse = forms.CharField(widget=forms.Textarea)
    mail = forms.CharField()
    phone = forms.CharField(required = False)

    id1 = forms.ImageField()
    id2 = forms.ImageField(required = False)
    situation = forms.ChoiceField(choices = SITUATION_INSCR_LIST_ELEC)
    situation_autre = forms.CharField(required=False)
    justificatif_adresse = forms.ImageField()

    def clean_id1(self):
        pic = self.cleaned_data['id1']
        if pic.size > 3300000: #3M to ensure the full mail will be below 10M
            raise forms.ValidationError(_("Merci de n'envoyer que des fichiers inférieurs à 3Mb. Taille du fichier courant : %s") % (filesizeformat(content._size)))
        return pic
    def clean_id2(self):
        pic = self.cleaned_data['id2']
        if pic :
            if pic.size > 3300000: #3M to ensure the full mail will be below 10M
                raise forms.ValidationError(_("Merci de n'envoyer que des fichiers inférieurs à 3Mb. Taille du fichier courant : %s") % (filesizeformat(content._size)))
        return pic
    def clean_justificatif_adresse(self):
        pic = self.cleaned_data['justificatif_adresse']
        if pic.size > 3300000: #3M to ensure the full mail will be below 10M
            raise forms.ValidationError(_("Merci de n'envoyer que des fichiers inférieurs à 3Mb. Taille du fichier courant : %s") % (filesizeformat(content._size)))
        return pic

    def genEmailTitle(self):
        return "Demande d'ajout sur les listes électorales"

    def genEmailContent(self):
        id_demandeur = self.cleaned_data['nom'].upper() + " " + self.cleaned_data['prenoms'].capitalize()

        mailContent = """
Demande d'ajout sur les listes électorales via la plateforme de démarche en ligne demarches-villages.fr \n \n
Le demandeur :
    Identité : """ + id_demandeur + """
    Adresse : """ + self.cleaned_data['adresse'] + """
    Telephone : """ + self.cleaned_data['phone'] + """
    Mail : """ + self.cleaned_data['mail'] + """
    situation : """ + self.cleaned_data['situation']
        if self.cleaned_data['situation'] == "Inscription pour un autre motif" :
            mailContent += " : " +  self.cleaned_data['situation_autre']

        mailContent += """ \n
Les pièces justificatives (papiers d'identité et justificatifs de domicile) sont disponibles en pièces jointes.
Attention ! Les fichiers n'ont pas été vérifiés par la plateforme mais simplement transmis.
Une fois téléchargés, vérifiez leur nature avant de les ouvrir
et ne les éxécutez pas s'il s'agit de programmes !"""

        return mailContent;
