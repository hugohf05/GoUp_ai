from datetime import date

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class EstatAtleta(models.TextChoices):
    ACTIU = 'ACTIU', _('Actiu')
    LESIONAT = 'LESIONAT', _('Lesionat')

class ActivitatFisicaDiaria(models.TextChoices):
    SEDENTARI = 'SEDENTARI', _('Sedentari')
    ACTIU = 'ACTIU', _('Actiu')
    MOLT_ACTIU = 'MOLT_ACTIU', _('Molt Actiu')

class TipusUbicacio(models.TextChoices):
    EXTERIOR = 'EXTERIOR', _('Exterior')
    INTERIOR = 'INTERIOR', _('Interior')

class TipusAlimentacio(models.TextChoices):
    VEGETARIA = 'VEGETARIA', _('Vegetarià')
    VEGA = 'VEGA', _('Vegà')
    OMNIVOR = 'OMNIVOR', _('Omnívor')

class EstatActual(models.TextChoices):
    ACTIVA = 'ACTIVA', _('Activa')
    REHABILITACIO = 'REHABILITACIO', _('Rehabilitació')
    RESOLTA = 'RESOLTA', _('Resolta')

class TipusSuperficie(models.TextChoices):
    ASFALT = 'ASFALT', _('Asfalt')
    CINTA = 'CINTA', _('Cinta')
    TRAIL = 'TRAIL', _('Trail')


class Atleta(models.Model):
    dni_atleta = models.CharField(max_length=20, primary_key=True, help_text="Document d'identitat (ex. 12345678X)")
    nom = models.CharField(max_length=100, help_text="Nom complet de l'atleta")
    data_naixement = models.DateField(help_text="Format: AAAA-MM-DD")
    correu = models.EmailField(max_length=150, unique=True, help_text="Adreça de correu electrònic vàlida")
    numero_telefon = models.CharField(max_length=20, unique=True, help_text="Telèfon de contacte amb prefix")
    pes = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Pes en kilograms (kg)")
    composicio_corporal = models.CharField(max_length=200, help_text="Ex: 15% greix, 45% massa muscular")
    altura = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Altura en metres (ex: 1.80)")
    objectiu = models.CharField(max_length=100, help_text="Objectiu principal (ex. Guanyar massa muscular, Pèrdua de pes)")
    activitat_fisica_diaria = models.CharField(max_length=15, choices=ActivitatFisicaDiaria.choices, help_text="Nivell d'activitat diària fora de l'entrenament")
    estat = models.CharField(max_length=10, choices=EstatAtleta.choices, help_text="Estat general actual de l'atleta")

    def __str__(self):
        return f"{self.nom} ({self.dni_atleta})"

    class Meta:
        verbose_name_plural = "Atletes"


class Alimentacio(models.Model):
    atleta = models.OneToOneField(Atleta, on_delete=models.RESTRICT, related_name='alimentacio', help_text="Atleta a qui pertany aquesta dieta")
    tipus_alimentacio = models.CharField(max_length=15, choices=TipusAlimentacio.choices, help_text="Preferència dietètica")
    calories = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Objectiu calòric diari (kcal)")
    proteina = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Grams de proteïna diaris (g)")
    carbohidrats = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Grams de carbohidrats diaris (g)")
    grases = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Grams de greixos diaris (g)")
    suplementacio = models.TextField(null=True, blank=True, help_text="Llista de suplements (opcional)")

    def __str__(self):
        return f"Alimentació de {self.atleta.nom}"

    class Meta:
        verbose_name_plural = "Alimentacions"


class Ubicacio(models.Model):
    tipus_ubicacio = models.CharField(max_length=10, choices=TipusUbicacio.choices, help_text="Lloc on es realitza l'entrenament")
    adreca = models.CharField(max_length=200, help_text="Nom del gimnàs, parc o adreça exacta")

    def __str__(self):
        return f"{self.get_tipus_ubicacio_display()} - {self.adreca}"

    class Meta:
        verbose_name_plural = "Ubicacions"


class Valoracio(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, help_text="Atleta que fa la valoració")
    ubicacio = models.ForeignKey(Ubicacio, on_delete=models.CASCADE, help_text="Ubicació valorada")
    valoracio = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], help_text="Puntuació del 0.0 al 5.0")
    comentaris = models.TextField(null=True, blank=True, help_text="Comentaris sobre les instal·lacions")

    class Meta:
        unique_together = ('atleta', 'ubicacio')
        verbose_name_plural = "Valoracions"

    def __str__(self):
        return f"{self.atleta.nom} valora ubicació {self.ubicacio.id} amb {self.valoracio}"


class Exercici(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='exercicis', help_text="Creador de l'exercici")
    nom = models.CharField(max_length=100, help_text="Nom descriptiu de l'exercici")
    descripcio = models.TextField(null=True, blank=True, help_text="Instruccions tècniques de l'exercici")
    descans_entre_series = models.DurationField(null=True, blank=True, help_text="Temps de descans suggerit (Format: HH:MM:SS)")

    def __str__(self):
        return f"{self.nom} (per {self.atleta.nom})"

    class Meta:
        verbose_name_plural = "Exercicis"


class SessioEntrenament(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, help_text="Atleta que realitza la sessió")
    ubicacio = models.ForeignKey(Ubicacio, on_delete=models.CASCADE, help_text="Lloc de la sessió")
    data = models.DateField(help_text="Data de la sessió d'entrenament (Format: AAAA-MM-DD)")
    duracio_total = models.DurationField(help_text="Duració completa de l'entrenament (Format: HH:MM:SS)")
    comentaris = models.TextField(null=True, blank=True, help_text="Sensacions i notes de l'entrenament")
    exercicis = models.ManyToManyField(Exercici, related_name='sessions', help_text="Llista d'exercicis a realitzar en aquesta sessió")

    def __str__(self):
        return f"Sessió de {self.atleta.nom} ({self.data})"

    class Meta:
        verbose_name_plural = "Sessions d'entrenament"


class Serie(models.Model):
    exercici = models.ForeignKey(Exercici, on_delete=models.CASCADE, related_name='%(class)s', help_text="Exercici al qual pertany la sèrie")
    num_serie = models.PositiveIntegerField(help_text="Número d'ordre d'aquesta sèrie")

    class Meta:
        abstract = True
        unique_together = ('exercici', 'num_serie')

    def __str__(self):
        return f"Sèrie {self.num_serie} de {self.exercici.nom}"


class Forca(Serie):
    grup_muscular = models.CharField(max_length=100, help_text="Múscul o grup muscular principal")
    pes = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Càrrega en kilograms (kg)")
    rpe = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], help_text="Percepció de l'esforç de 0 a 10 (Rate of Perceived Exertion)")

    def __str__(self):
        return super().__str__() + " (Força)"

    class Meta:
        verbose_name_plural = "Sèries de Força"


class Resistencia(Serie):
    duracio = models.DurationField(help_text="Duració d'aquesta sèrie (Format: HH:MM:SS)")
    tipus_superficie = models.CharField(max_length=10, choices=TipusSuperficie.choices, help_text="Terreny on s'ha realitzat")
    distancia = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Distància recorreguda en kilòmetres (km)")
    desnivell = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Desnivell positiu acumulat en metres (m)")
    freq_cardiaca_mitjana = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(30), MaxValueValidator(220)], help_text="Mitjana de pulsacions per minut (bpm)")

    def __str__(self):
        return super().__str__() + " (Resistència)"

    class Meta:
        verbose_name_plural = "Sèries de Resistència"


class Lesio(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lesions', help_text="Atleta que pateix la lesió")
    data_inici = models.DateField(help_text="Data en què es va produir o diagnosticar (Format: AAAA-MM-DD)")
    data_fi = models.DateField(null=True, blank=True, help_text="Data de curació total. Deixar en blanc si encara està activa. (Format: AAAA-MM-DD)")
    zona_afectada = models.CharField(max_length=100, help_text="Part del cos lesionada (ex. Genoll dret, Espatlla)")
    grau_serietat = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], help_text="Escala de gravetat de 0 (lleu) a 5 (molt greu)")
    estat_actual = models.CharField(max_length=15, choices=EstatActual.choices, help_text="Estat de recuperació de la lesió")
    comentaris_diagnostic = models.TextField(null=True, blank=True, help_text="Diagnòstic mèdic o descripció detallada")

    def clean(self):
        from django.core.exceptions import ValidationError

        # 1. data_inici <= data_fi
        if self.data_inici and self.data_fi:
            if self.data_inici > self.data_fi:
                raise ValidationError({"data_fi": "La data de finalització no pot ser anterior a la data d'inici."})

        # 2. Coherència entre estat_actual i data_fi
        if self.estat_actual in [EstatActual.ACTIVA, EstatActual.REHABILITACIO]:
            if self.data_fi is not None:
                raise ValidationError({
                    "data_fi": f"Una lesió en estat '{self.get_estat_actual_display()}' no pot tenir data de finalització."
                })
        elif self.estat_actual == EstatActual.RESOLTA:
            if not self.data_fi:
                raise ValidationError({
                    "data_fi": "Una lesió resolta ha de tenir obligatòriament una data de finalització."
                })
            if self.data_fi > date.today():
                raise ValidationError({
                    "data_fi": "La data de finalització d'una lesió resolta no pot ser en el futur."
                })

    def __str__(self):
        return f"Lesió {self.zona_afectada} ({self.atleta.nom})"

    class Meta:
        verbose_name_plural = "Lesions"


class Descans(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='descansos', help_text="Atleta al qual pertany aquest registre de son")
    data_inici = models.DateTimeField(help_text="Dia i hora d'anar a dormir")
    duracio = models.PositiveIntegerField(help_text="Duració total de la sessió de son en minuts")
    despert = models.PositiveIntegerField(help_text="Temps despert durant la nit en minuts")
    rem = models.PositiveIntegerField(help_text="Temps en fase REM en minuts")
    core = models.PositiveIntegerField(help_text="Temps en fase de son lleuger (Core) en minuts")
    deep = models.PositiveIntegerField(help_text="Temps en fase de son profund (Deep) en minuts")
    hrv = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Variabilitat de la Freqüència Cardíaca en mil·lisegons (ms)")

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # La duració ha de ser exactament la suma de les 4 fases de son
        suma_fases = (self.despert or 0) + (self.rem or 0) + (self.core or 0) + (self.deep or 0)
        
        if self.duracio and suma_fases != self.duracio:
            raise ValidationError({
                "duracio": f"La duració total ({self.duracio} minuts) ha de ser igual a la suma de les 4 fases de descans ({suma_fases} minuts)."
            })

    class Meta:
        unique_together = ('atleta', 'data_inici')
        verbose_name_plural = "Descansos"

    def __str__(self):
        return f"Descans de {self.atleta.nom} ({self.data_inici})"


class RegistreDiari(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='registres', help_text="Atleta que omple el registre")
    # CANVI: de auto_now_add=True a default=date.today perquè sigui assignable manualment
    # (necessari per a bulk_create amb dates històriques) i editable des de l'admin si cal.
    data = models.DateField(default=date.today, help_text="Data del registre (per defecte avui)")
    adaptabilitat_alimentacio = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)], help_text="Percentatge d'adherència a la dieta establerta (0-100%)")
    comentaris_entrenaments = models.TextField(null=True, blank=True, help_text="Comentaris sobre l'esforç, la motivació o incidents")
    estat_recuperacio_descans = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], help_text="Sensació de recuperació al despertar (0.0 a 5.0)")
    nivell_energia = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], help_text="Nivell d'energia percebut durant el dia (0.0 a 5.0)")
    nivell_estres = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], help_text="Nivell d'estrès emocional o físic (0.0 a 5.0)")
    sensacions_generals = models.TextField(null=True, blank=True, help_text="Notes generals, dolors, estat d'ànim, etc.")

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Si estem creant un registre nou i l'atleta ja en té un per avui, llancem error visual
        if not self.pk and hasattr(self, 'atleta') and self.atleta:
            if RegistreDiari.objects.filter(atleta=self.atleta, data=date.today()).exists():
                raise ValidationError({
                    "atleta": "Aquest atleta ja té un Registre Diari creat avui! Tria'n un altre."
                })

    class Meta:
        unique_together = ('atleta', 'data')
        verbose_name_plural = "Registres Diaris"

    def __str__(self):
        return f"Registre {self.data} - {self.atleta.nom}"


class InformeIA(models.Model):
    # Relació 1:1 obligatòria: cada RegistreDiari té exactament un InformeIA.
    # La FK viu aquí (InformeIA → RegistreDiari) perquè Django no permet
    # referències circulars entre models al mateix nivell.
    # S'accedeix des del registre amb: registre.informeIA
    registre_diari = models.OneToOneField(
        RegistreDiari,
        on_delete=models.CASCADE,   # CANVI: CASCADE perquè si s'esborra el registre, s'esborra l'informe
        related_name='informeIA',
        help_text="Registre diari al qual s'associa aquest informe"
    )
    recomanacio_entrenament = models.TextField(help_text="Anàlisi i suggeriments d'entrenament generats per l'IA")
    recomanacio_alimentacio = models.TextField(help_text="Anàlisi i suggeriments d'alimentació generats per l'IA")
    recomanacio_descans = models.TextField(help_text="Anàlisi i suggeriments de descans generats per l'IA")

    def __str__(self):
        return f"Informe IA per {self.registre_diari}"

    class Meta:
        verbose_name_plural = "Informes IA"