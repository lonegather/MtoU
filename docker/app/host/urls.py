"""host URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from main import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', views.api, name='api'),
    path('', views.index, name='index'),
    path('help/', views.doc, name='help'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('object_delete/<uuid:object_id>', views.object_delete, name='object_delete'),
    path('<uuid:project_id>/<uuid:genus_id>/', views.index_project, name='index_project'),
    path('<uuid:project_id>/entity/<uuid:entity_id>/', views.index_entity, name='index_entity'),
    path('<uuid:project_id>/help/<str:episode>', views.doc_episode, name='help_episode'),
    path('<uuid:project_id>/settings/', views.settings, name='settings'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
