from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('admin/',views.adminView, name = 'adminView'),
    path('admin_demo/',views.demoAdminView, name = 'demoAdminView'),
    path('inscription/',views.registerPage, name='inscription'),
    path('connexion/',views.loginPage, name='login'),
    path("deconnexion/", views.logoutRequest, name='logout'),
    path('modification_mot_de_passe/',
        auth_views.PasswordChangeView.as_view(
            template_name='village_instance/change_password.html',
            success_url = reverse_lazy('adminView')
        ),
        name='change_password'
        ),
    path('<str:url_city_name>/',views.citizenView, name='citizenView'),
    path('<str:url_city_name>/<str:url_form_name>/',views.formView, name='formView'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
