from django.contrib import admin
from .models import (
    Atleta, Alimentacio, Ubicacio, Valoracio, Exercici, 
    SessioEntrenament, Forca, Resistencia, Lesio, 
    Descans, RegistreDiari, InformeIA
)

@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ('dni_atleta', 'nom', 'objectiu', 'estat')
    search_fields = ('dni_atleta', 'nom', 'correu')
    list_filter = ('estat', 'activitat_fisica_diaria')

@admin.register(Ubicacio)
class UbicacioAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipus_ubicacio', 'adreca')
    list_filter = ('tipus_ubicacio',)

@admin.register(SessioEntrenament)
class SessioAdmin(admin.ModelAdmin):
    list_display = ('id', 'atleta', 'ubicacio', 'data', 'duracio_total')
    list_filter = ('data',)
    search_fields = ('atleta__nom',)

@admin.register(Exercici)
class ExerciciAdmin(admin.ModelAdmin):
    list_display = ('nom', 'atleta')
    search_fields = ('nom', 'atleta__nom')

# Registrem de manera simple els altres models
admin.site.register(Alimentacio)
admin.site.register(Valoracio)
admin.site.register(Forca)
admin.site.register(Resistencia)
admin.site.register(Lesio)
admin.site.register(Descans)
admin.site.register(RegistreDiari)
admin.site.register(InformeIA)
