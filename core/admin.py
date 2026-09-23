from django.contrib import admin

from .models import Cliente, Maquina


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj_cpf", "contato", "ativo")
    search_fields = ("nome", "cnpj_cpf")
    list_filter = ("ativo",)


@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ("identificador", "descricao", "ativo")
    search_fields = ("identificador", "descricao")
    list_filter = ("ativo",)
