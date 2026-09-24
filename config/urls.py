from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("checklist/", include("checklist.urls")),
]

if settings.MEDIA_BACKEND == "local":
    # Fora do modo DEBUG o Django normalmente não serve mídia sozinho — aqui
    # forçamos isso de propósito, já que é um deploy simples de teste numa
    # única VPS pequena (sem Nginx na frente). Para uso com tráfego real
    # valeria colocar um Nginx servindo /media/ diretamente do disco.
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]