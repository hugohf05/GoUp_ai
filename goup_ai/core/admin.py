from django.contrib import admin
from .models import (
    Atleta, Alimentacio, Ubicacio, Valoracio, Exercici, 
    SessioEntrenament, Forca, Resistencia, Lesio, 
    Descans, RegistreDiari, InformeIA
)

# Optimització global per a bases de dades massives
class MassDataModelAdmin(admin.ModelAdmin):
    show_full_result_count = False  # Evita el SELECT COUNT(*) lent
    list_per_page = 50              # Paginació més lleugera

@admin.register(Atleta)
class AtletaAdmin(MassDataModelAdmin):
    list_display = ('dni_atleta', 'nom', 'objectiu', 'estat')
    search_fields = ('dni_atleta', 'nom', 'correu')
    list_filter = ('estat', 'activitat_fisica_diaria')

@admin.register(Ubicacio)
class UbicacioAdmin(MassDataModelAdmin):
    list_display = ('id', 'tipus_ubicacio', 'adreca')
    list_filter = ('tipus_ubicacio',)

@admin.register(SessioEntrenament)
class SessioAdmin(MassDataModelAdmin):
    list_display = ('id', 'atleta', 'ubicacio', 'data', 'duracio_total')
    list_filter = ('data',)
    search_fields = ('atleta__dni_atleta', 'atleta__nom')
    raw_id_fields = ('atleta', 'ubicacio')
    autocomplete_fields = ['exercicis']
    list_select_related = ('atleta', 'ubicacio')

@admin.register(Exercici)
class ExerciciAdmin(MassDataModelAdmin):
    list_display = ('id', 'nom', 'atleta')
    search_fields = ('nom',)
    raw_id_fields = ('atleta',)
    list_select_related = ('atleta',)

@admin.register(Alimentacio)
class AlimentacioAdmin(MassDataModelAdmin):
    raw_id_fields = ('atleta',)
    list_select_related = ('atleta',)

@admin.register(Valoracio)
class ValoracioAdmin(MassDataModelAdmin):
    raw_id_fields = ('atleta', 'ubicacio')
    list_select_related = ('atleta', 'ubicacio')

@admin.register(Forca)
class ForcaAdmin(MassDataModelAdmin):
    raw_id_fields = ('exercici',)
    list_select_related = ('exercici',)

@admin.register(Resistencia)
class ResistenciaAdmin(MassDataModelAdmin):
    raw_id_fields = ('exercici',)
    list_select_related = ('exercici',)

@admin.register(Lesio)
class LesioAdmin(MassDataModelAdmin):
    list_display = ('zona_afectada', 'atleta', 'data_inici', 'estat_actual')
    raw_id_fields = ('atleta',)
    list_select_related = ('atleta',)

@admin.register(Descans)
class DescansAdmin(MassDataModelAdmin):
    raw_id_fields = ('atleta',)
    list_select_related = ('atleta',)

@admin.register(RegistreDiari)
class RegistreDiariAdmin(MassDataModelAdmin):
    readonly_fields = ('data',)
    raw_id_fields = ('atleta',)
    list_select_related = ('atleta',)

@admin.register(InformeIA)
class InformeIAAdmin(MassDataModelAdmin):
    raw_id_fields = ('registre_diari',)
    list_select_related = ('registre_diari',)
