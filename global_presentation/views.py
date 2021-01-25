from django.shortcuts import render, redirect
from village_instance.forms import CityDropDownForm

from django.contrib import messages

# Create your views here.

def home(request):
	cityDropDownForm = CityDropDownForm(request.POST or None)

	# if a city has been selected in the dropdown list
	if request.method == 'POST' :
		if cityDropDownForm.is_valid():
			url_city_name = cityDropDownForm.cleaned_data['city'].url
			return redirect('citizenView', url_city_name=url_city_name)
		else :
			messages.error(request,cityDropDownForm.errors)

	context = {'cityDropDownForm':cityDropDownForm,
				"home_page": "active",
				}
	return render(request, 'global_presentation/home.html', context)

def faq(request):
	context = {"faq_page": "active",}
	return render(request, 'global_presentation/faq.html', context)

def tos(request):
	context = {"tos_page": "active",}
	return render(request, 'global_presentation/tos.html', context)

def searchCity(request):
	cityDropDownForm = CityDropDownForm(request.POST or None)
	if request.method == 'POST' :
		if cityDropDownForm.is_valid():
			url_city_name = cityDropDownForm.cleaned_data['city'].url
			return redirect('citizenView', url_city_name=url_city_name)
		else :
			messages.error(request,cityDropDownForm.errors)

	context = {'cityDropDownForm':cityDropDownForm,
				}
	return render(request, 'global_presentation/city_search.html', context)
