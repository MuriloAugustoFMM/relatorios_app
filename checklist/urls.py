from django.urls import path

from . import views

app_name = "checklist"

urlpatterns = [
    path("novo/", views.novo_checklist, name="novo"),
    path("maquinas/buscar/", views.buscar_maquinas, name="buscar_maquinas"),
    path("buscar/", views.buscar_checklists, name="buscar"),
    path("<int:pk>/", views.detalhe_checklist, name="detalhe"),
    path("<int:pk>/pdf/", views.gerar_pdf_checklist, name="gerar_pdf"),
    path("<int:pk>/preview/", views.visualizar_checklist, name="preview"),
]