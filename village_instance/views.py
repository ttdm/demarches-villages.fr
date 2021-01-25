from django.shortcuts import render, redirect
from .forms import *
from django.utils.safestring import mark_safe

from django.core.mail import EmailMessage

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.models import User
from .models import *

# Create your views here.
def citizenView(request, url_city_name):
	curCity = City()
	try:
		curCity = City.objects.get(url=url_city_name)
	except curCity.DoesNotExist:
		cityDropDownForm = CityDropDownForm()
		context = { 'city_name': url_city_name,
					'cityDropDownForm': cityDropDownForm}
		return render(request, 'village_instance/not_found.html', context)

	listOfActivatedForms = curCity.forms.all().order_by('name_descrip')
	listOfActivatedCategories = listOfActivatedForms.values_list("category",flat=True).distinct()
	listOfAllCategories = ['Etat Civil', 'Signalement', 'Divers']
	# Previous line isn't pretty, it needs to be manually updated,
	# but it allow to choose the categories order instead of letting it to the database


	demo = False
	if curCity.name == "Démonstration" :
		demo = True

	context = { 'citizen_page': 'text-active',
				'accueil': True,
				'city': curCity,
				'listOfActivatedForms' : listOfActivatedForms,
				'listOfActivatedCategories' : listOfActivatedCategories,
				'listOfAllCategories': listOfAllCategories,
				'demo' : demo,
				}
	return render(request, 'village_instance/city_page.html', context)


def formView(request, url_city_name, url_form_name):
	# get city data from request
	curCity = City()
	try:
		curCity = City.objects.get(url=url_city_name)
	except curCity.DoesNotExist:
		cityDropDownForm = CityDropDownForm()
		context = { 'city_name': url_city_name,
					'cityDropDownForm': cityDropDownForm}
		return render(request, 'village_instance/not_found.html', context)

	# get selected form from request
	curFormObject = Forms()
	try:
		curFormObject = Forms.objects.get(url=url_form_name)
	except curFormObject.DoesNotExist:
		messages.info(request, """Vous venez de tenter d'accéder à un formulaire non accessible.
				La liste des formulaires disponibles pour votre commune est disponible sur la page actuelle.""")
		return redirect('citizenView', url_city_name=url_city_name)

	# create selected form and extract data from it
	formConstructor = None
	lat = 0
	lng = 0
	if curFormObject.category == 'Signalement':
		formConstructor = globals()["SignalementForm"]
		lat = 45.1630 #TODO add in city model
		lng = 5.9268
	else:
		formConstructor = globals()[curFormObject.name_id+"Form"]
	form = formConstructor(request.POST or None, request.FILES or None)

	formFilledContent = ''
	if form.is_valid():
		if curCity.name == "Démonstration" :
			messages.info(request, """En dehors de cette démonstration, votre demande aurait bien été transmise.""")
			return redirect('citizenView', url_city_name=url_city_name)
		mailTitle = ''
		mailContent =''
		if curFormObject.category == 'Signalement':
			mailTitle = form.genEmailTitle(curFormObject.name_descrip)
			mailContent = form.genEmailContent(curFormObject.name_descrip)
		else :
			mailTitle = form.genEmailTitle()
			mailContent = form.genEmailContent()

		email = EmailMessage(
		    subject = 'Démarche en ligne : ' + mailTitle,
		    body = mailContent,
		    from_email = None,
		    to = [curCity.user.email],
		)
		if curFormObject.category == 'Signalement':
			pic1 = form.cleaned_data['pic1']
			if pic1 :
				email.attach(pic1.name, pic1.read(), pic1.content_type)
			pic2 = form.cleaned_data['pic2']
			if pic2 :
				email.attach(pic2.name, pic2.read(), pic2.content_type)
		if curFormObject.name_id == 'AjoutListeElectorale':
			id1 = form.cleaned_data['id1']
			if id1 :
				email.attach(id1.name, id1.read(), id1.content_type)
			id2 = form.cleaned_data['id2']
			if id2 :
				email.attach(id2.name, id2.read(), id2.content_type)
			justificatif_adresse = form.cleaned_data['justificatif_adresse']
			if justificatif_adresse :
				email.attach(justificatif_adresse.name, justificatif_adresse.read(), justificatif_adresse.content_type)
		email.send(fail_silently=True) #TODO work to get data if fail to send it back manually
					# or better automatically once more; and check manually if 2 fails.
					#anyway, a fail strategy should be added.
		messages.info(request, """Votre demande a bien été transmise. Vous devriez recevoir un mail
				de la commune à propos de celle-ci dans les jours qui arrivent. """)
		return redirect('citizenView', url_city_name=url_city_name)

	context ={	'formcontent': formFilledContent,
				'city': curCity,
				'form': form,
				'formObject':curFormObject,
				'lat': lat,
				'lng': lng,
				}
	templateTorender = ''
	if curFormObject.category == 'Signalement':
		templateTorender = 'village_instance/forms/signalements.html'
	else:
		templateTorender = 'village_instance/forms/'+curFormObject.url+'.html'
	form = formConstructor(request.POST or None)

	return render(request, templateTorender, context)


def adminView(request):
	if request.user.is_authenticated == False:
		msgString = "Vous devez <a href='/connexion/'>vous connecter</a> pour accéder au pannel admin !"
		# smth along the following line would be better
		# (url change automatically in the framework) (currently doesnt work)
		#msgString = "Vous devez <a href=\"{% url 'login' %}\">vous connecter</a> pour accéder au pannel admin !"
		messages.info(request, mark_safe(msgString))
		return redirect('login')

	# find which city is to be adminstrated (linked to connected user)
	userCity = City.objects.get(user=request.user)

	# load the list of all existing forms
	allForms = Forms.objects.all().order_by('name_id').order_by('category')

	## Handle form reception
	if request.method == 'POST':
		if 'forms' in request.POST:
			allCheckboxes = ActivationCheckboxes(request.POST, questions=allForms)
			if allCheckboxes.is_valid():
				messages.success(request, "Vos changements ont bien étés pris en compte.")
				for (question, answer) in allCheckboxes.reformat_checkboxes():
					if answer :
						userCity.forms.add(Forms.objects.get(name_id=question))
					else :
						userCity.forms.remove(Forms.objects.get(name_id=question))
		if 'profile' in request.POST:
			accountForm = UserMailOnly(request.POST, instance=userCity.user)
			profile_form = CityModifForm(request.POST, request.FILES or None, instance=userCity)
			if accountForm.is_valid() and profile_form.is_valid():
				messages.success(request, "Vos changements ont bien étés pris en compte.")
				profile_form.save()
				accountForm.save()

	## Create forms.
	# Create forms to modify the account and profile informations
	profileForm = CityModifForm(None, instance=userCity)
	accountForm = UserMailOnly(None, instance=userCity.user)

	# create the checkboxes to let the admin choose the activation of each form
	allCheckboxes = ActivationCheckboxes(None, questions=allForms)

	## Modify checkboxes to fit current state
	# get currently active forms for usercity to default check them
	activForms = userCity.forms.all()

	# set the checkboxes to true if previously allowed by administrators
	for _,question in allCheckboxes.fields.items():
		correspondingForm = Forms.objects.get(name_id=question.label)
		# note : label is defined as name_id in forms.py,  ActivationCheckboxes __init__ declaration
		if (correspondingForm in activForms) :
			question.initial = True

	# link informations to be displayed on each form
	# and the correspoding checkbox
	zippedFormsCheckBoxes = zip(allForms,allCheckboxes)

	context = {	'city': userCity,
				'admin_page': "text-active",
				'zippedFormsCheckBoxes':zippedFormsCheckBoxes,
				'tmp': allCheckboxes,
				'profile_form': profileForm,
				'account_form' : accountForm,
				}
	return render(request, 'village_instance/admin_city_page.html', context)

def registerPage(request):
	if request.method == 'POST':
		form = ReducedUserCreationForm(request.POST)
		profile_form = CityRegisterForm(request.POST, request.FILES or None)

		if form.is_valid() and profile_form.is_valid():
			# create user
			user = form.save()
			profile = profile_form.save(commit=False)
			profile.user = user
			profile.save()
			messages.info(request, "Votre compte a bien été créé, vous êtes maintenant connecté sur la page admin de votre ville.")
			new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])

			#login and redirect
			login(request, new_user)
			return redirect('login')

	else:
		form = ReducedUserCreationForm()
		profile_form = CityRegisterForm()

	context= {'form': form,
			'profile_form': profile_form,
			"inscrip_page": "active",
			}
	return render(request, 'village_instance/inscription.html', context)


def loginPage(request):
	if request.user.is_authenticated:
		return redirect('adminView')
	else:
		if request.method == 'POST':
			username = request.POST.get('username')
			password = request.POST.get('password')

			user = authenticate(request, username=username, password=password)

			#TODO NOT SURE FOLLOWING 3 LINES WORK to redirect to specific admin user page
			#NOT CLEAN IF IT WORKS ! (direct url instead of generic name + arg )
			if user is not None:
				login(request, user)
				userCity = City.objects.get(user=user)
				return redirect("adminView")
			else:
				messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

		context = {}
		return render(request, 'village_instance/login.html', context)

def logoutRequest(request):
	if request.user.is_authenticated:
		userCity = City.objects.get(user=request.user)
		logout(request)
		messages.success(request, "Vous êtes maintenant déconnecté !")
		return redirect('citizenView', url_city_name=userCity.url)
	return redirect('home')

def demoAdminView(request):
	# Load Demo informations (logo, name ...)
	userCity = City.objects.get(name="Démonstration")
	# load all possible forms
	allForms = Forms.objects.all()
	# create the checkboxes to let the admin choose the activation of each form
	allCheckboxes = ActivationCheckboxes(None, questions=allForms)

	# set all the checkboxes to true
	for _,question in allCheckboxes.fields.items():
			question.initial = True

	profileForm = CityRegisterForm(None,instance=userCity)

	# link informations to be displayed on each form
	# and the correspoding checkbox
	zippedFormsCheckBoxes = zip(allForms,allCheckboxes)
	context = {	'admin_page': 'text-active',
				'city': userCity,
				'zippedFormsCheckBoxes':zippedFormsCheckBoxes,
				'demo' : True,
				'profile_form' : profileForm,
				}
	return render(request, 'village_instance/admin_city_page.html', context)
