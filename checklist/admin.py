from django.contrib import admin

from .models import Checklist, ItemChecklist, Foto


class ItemChecklistInline(admin.TabularInline):
    model = ItemChecklist
    extra = 1


class FotoInline(admin.TabularInline):
    model = Foto
    extra = 1
    fields = ("imagem", "item", "legenda")


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "maquina", "cliente", "data", "responsavel")
    list_filter = ("tipo", "cliente", "data")
    search_fields = ("titulo", "maquina__identificador", "cliente__nome")
    autocomplete_fields = ("maquina", "cliente")
    readonly_fields = ("titulo", "pdf_gerado")
    inlines = [ItemChecklistInline, FotoInline]


@admin.register(ItemChecklist)
class ItemChecklistAdmin(admin.ModelAdmin):
    list_display = ("pergunta", "checklist", "resultado")
    list_filter = ("resultado",)


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ("id", "checklist", "item", "tirada_em")
    list_filter = ("checklist__tipo",)
