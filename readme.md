# Demarches-villages.fr

Une plateforme de dématérialisation à destination des petites communes basée sur le framework django.

Le code du repo est configuré pour être instantanément utilisable en local pourqu'il soit possible d'implémenter de tester des modifs rapidement. La configuration utilisée sur le serveur est légèrement différente (Db, mail server, static file handling, security...)

## Installation locale

#### Dépendances :

django (3.1), pillow, django-leaflet, gdal

Pour la plupart des utilisateurs, [l'installation de django](https://docs.djangoproject.com/en/3.1/intro/install/) est un simple  :

		pip install django

Les autres dépendances :

		sudo apt install libgdal-dev
		pip install pillow django-leaflet gdal

#### demarches-villages.fr

		git clone https://github.com/ttdm/demarches-villages.fr

Pour démarrer le serveur local :

		cd demarches-villages.fr
		python manage.py runserver

Pour accéder au site hébergé localement : http://127.0.0.1:8000/

La base de donnée sqlite fournie comporte une ville, la ville de démonstration, ainsi que la totalité des formulaires disponibles pour les mairies. L'utilisateur associé à la ville de démonstration et superutilisateur du projet est 'admin' avec comme password : 'pass'

## Contributions

Elles sont bien évidemment acceptées avec plaisir. N'en attendant pas des dizaines, vous pouvez au choix ouvrir une 'issue', faire un pull request ou me contacter par mail (thibaut.tezenas(at)protonmail.com).

## License & Auteur

Ce repo est sous license  CC BY-NC-SA 3.0, le texte de la license est disponible dans le repo.
En cas de réutilisation, l'auteur à citer est Thibaut Tezenas du Montcel.
Sans accord écrit différent, la mention "Auteur Originel : <a href="https://ttdm.github.io/">Thibaut Tezenas Du Montcel</a>" doit apparaitre pour les visiteurs sur chacune des pages créées grâce à ce code. Contactez moi directement à thibaut.tezenas(at)protonmail.com si vous souhaitez qu'il en soit autrement et on pourra en discuter.
