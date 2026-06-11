from django import forms
from .models import Atleta, Lesio, SessioEntrenament, Valoracio, Exercici, RegistreDiari, Alimentacio, Descans, Ubicacio

class AtletaAjaxFormMixin:
    """
    Mixin antic per AJAX. Ara permet carregar tots els atletes al Select2 local
    ja que el nombre d'atletes és petit (300) i així garantim que la cerca 
    funciona a l'instant i sense dependre d'Internet o la velocitat de la BD.
    """
    def init_atleta_queryset(self):
        if 'atleta' in self.fields:
            self.fields['atleta'].queryset = Atleta.objects.all().order_by('nom')


class AtletaForm(forms.ModelForm):
    class Meta:
        model = Atleta
        fields = [
            'dni_atleta', 'nom', 'data_naixement', 'correu', 'numero_telefon', 
            'pes', 'composicio_corporal', 'altura', 'objectiu', 
            'activitat_fisica_diaria', 'estat'
        ]
        widgets = {
            'dni_atleta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12345678X'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'data_naixement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'correu': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correu@example.com'}),
            'numero_telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+34600000000'}),
            'pes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'composicio_corporal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15% greix'}),
            'altura': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'objectiu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ironman'}),
            'activitat_fisica_diaria': forms.Select(attrs={'class': 'form-control'}),
            'estat': forms.Select(attrs={'class': 'form-control'}),
        }


class LesioForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = Lesio
        fields = [
            'atleta', 'zona_afectada', 'grau_serietat', 
            'data_inici', 'data_fi', 'estat_actual', 'comentaris_diagnostic'
        ]
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'zona_afectada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Genoll dret'}),
            'grau_serietat': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5'}),
            'data_inici': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estat_actual': forms.Select(attrs={'class': 'form-control'}),
            'comentaris_diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Detalls mèdics...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()


class SessioForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = SessioEntrenament
        fields = ['atleta', 'ubicacio', 'data', 'duracio_total', 'comentaris', 'exercicis']
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'ubicacio': forms.Select(attrs={'class': 'form-control select2'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duracio_total': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'step': '1'}),
            'comentaris': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'exercicis': forms.SelectMultiple(attrs={'class': 'form-control select2-ajax-exercicis', 'style': 'min-height: 150px;'}),
        }

    def __init__(self, *args, **kwargs):
        athlete_instance = kwargs.pop('athlete', None)
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()
        
        # Rendiment: Perquè la llista d'exercicis és molt gran, usem AJAX en lloc de carregar-los tots.
        # Només validem els exercicis que hagin estat seleccionats.
        if hasattr(self, 'data') and self.data and self.data.getlist('exercicis'):
            exercicis_ids = self.data.getlist('exercicis')
            self.fields['exercicis'].queryset = Exercici.objects.filter(id__in=exercicis_ids)
        elif self.instance and self.instance.pk:
            self.fields['exercicis'].queryset = self.instance.exercicis.all()
        else:
            self.fields['exercicis'].queryset = Exercici.objects.none()
            
        # Agrupar Ubicacions per Tipus (Interior / Exterior)
        from .models import Ubicacio
        ubicacions = Ubicacio.objects.all()
        choices = [('', '---------')]
        interiors = [(u.id, u.adreca) for u in ubicacions if u.tipus_ubicacio == 'INTERIOR']
        exteriors = [(u.id, u.adreca) for u in ubicacions if u.tipus_ubicacio == 'EXTERIOR']
        if interiors:
            choices.append(('Interior', interiors))
        if exteriors:
            choices.append(('Exterior', exteriors))
        self.fields['ubicacio'].choices = choices


class ValoracioForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = Valoracio
        fields = ['atleta', 'ubicacio', 'valoracio', 'comentaris']
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'ubicacio': forms.Select(attrs={'class': 'form-control'}),
            'valoracio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '5.0', 'placeholder': '0.0 - 5.0'}),
            'comentaris': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Opinió sobre les instal·lacions...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()


class RegistreDiariForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = RegistreDiari
        fields = [
            'atleta', 'data', 'adaptabilitat_alimentacio', 'comentaris_entrenaments',
            'estat_recuperacio_descans', 'nivell_energia', 'nivell_estres', 'sensacions_generals'
        ]
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'adaptabilitat_alimentacio': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'placeholder': '0 - 100%'}),
            'comentaris_entrenaments': forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'placeholder': 'Comentaris dels entrenaments d\'avui...'}),
            'estat_recuperacio_descans': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '5.0', 'placeholder': '0.0 - 5.0'}),
            'nivell_energia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '5.0', 'placeholder': '0.0 - 5.0'}),
            'nivell_estres': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '5.0', 'placeholder': '0.0 - 5.0'}),
            'sensacions_generals': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Sensacions generals, dolors, fatiga...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()


class AlimentacioForm(forms.ModelForm):
    class Meta:
        model = Alimentacio
        fields = ['tipus_alimentacio', 'calories', 'proteina', 'carbohidrats', 'grases', 'suplementacio']
        widgets = {
            'tipus_alimentacio': forms.Select(attrs={'class': 'form-control select2'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 2500'}),
            'proteina': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 150'}),
            'carbohidrats': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 300'}),
            'grases': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 80'}),
            'suplementacio': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Llistat de suplements (Whey, Creatina, etc.)'}),
        }


class ExerciciForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = Exercici
        fields = ['atleta', 'nom', 'descripcio', 'descans_entre_series']
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'exercici"}),
            'descripcio': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Instruccions tècniques...'}),
            'descans_entre_series': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'step': '1'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()
        

class DescansForm(AtletaAjaxFormMixin, forms.ModelForm):
    class Meta:
        model = Descans
        fields = ['atleta', 'data_inici', 'despert', 'rem', 'core', 'deep', 'duracio', 'hrv']
        widgets = {
            'atleta': forms.Select(attrs={'class': 'form-control select2'}),
            'data_inici': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'despert': forms.NumberInput(attrs={'class': 'form-control rests-input', 'min': '0'}),
            'rem': forms.NumberInput(attrs={'class': 'form-control rests-input', 'min': '0'}),
            'core': forms.NumberInput(attrs={'class': 'form-control rests-input', 'min': '0'}),
            'deep': forms.NumberInput(attrs={'class': 'form-control rests-input', 'min': '0'}),
            'duracio': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'hrv': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_atleta_queryset()

class UbicacioForm(forms.ModelForm):
    class Meta:
        model = Ubicacio
        fields = ['tipus_ubicacio', 'adreca']
        widgets = {
            'tipus_ubicacio': forms.Select(attrs={'class': 'form-control select2'}),
            'adreca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom del gimnàs, parc o adreça exacta"}),
        }
