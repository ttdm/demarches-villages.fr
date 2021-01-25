from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('faq/',views.faq, name='faq'),
    path('CGU/',views.tos, name='tos'),
    path('recherche/',views.searchCity, name = 'searchCity'),
]
