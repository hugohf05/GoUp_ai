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
    dni_atleta = models.CharField(max_length=20, primary_key=True)
    nom = models.CharField(max_length=100)
    data_naixement = models.DateField()
    correu = models.EmailField(max_length=150, unique=True)
    numero_telefon = models.CharField(max_length=20, unique=True)
    pes = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    composicio_corporal = models.CharField(max_length=200)
    altura = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    objectiu = models.CharField(max_length=100)
    activitat_fisica_diaria = models.CharField(max_length=15, choices=ActivitatFisicaDiaria.choices)
    estat = models.CharField(max_length=10, choices=EstatAtleta.choices)

    def __str__(self):
        return f"{self.nom} ({self.dni_atleta})"


class Alimentacio(models.Model):
    atleta = models.OneToOneField(Atleta, on_delete=models.CASCADE, related_name='alimentacio')
    tipus_alimentacio = models.CharField(max_length=15, choices=TipusAlimentacio.choices)
    calories = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    proteina = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    carbohidrats = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    grases = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    suplementacio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Alimentació de {self.atleta.nom}"


class Ubicacio(models.Model):
    # En Django, id és automàtic (AutoField) per defecte si no indiquem res, la qual cosa és id_ubicacio
    tipus_ubicacio = models.CharField(max_length=10, choices=TipusUbicacio.choices)
    adreca = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.get_tipus_ubicacio_display()} - {self.adreca}"


class Valoracio(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    ubicacio = models.ForeignKey(Ubicacio, on_delete=models.CASCADE)
    valoracio = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    comentaris = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('atleta', 'ubicacio')

    def __str__(self):
        return f"{self.atleta.nom} valora ubicació {self.ubicacio.id} amb {self.valoracio}"


class Exercici(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='exercicis_creats')
    nom = models.CharField(max_length=100)
    descripcio = models.TextField(null=True, blank=True)
    descans_entre_series = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} (per {self.atleta.nom})"


class SessioEntrenament(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    ubicacio = models.ForeignKey(Ubicacio, on_delete=models.PROTECT)
    data = models.DateField()
    duracio_total = models.DurationField()
    comentaris = models.TextField(null=True, blank=True)
    exercicis = models.ManyToManyField(Exercici, related_name='sessions')

    def __str__(self):
        return f"Sessió de {self.atleta.nom} ({self.data})"


class Serie(models.Model):
    exercici = models.ForeignKey(Exercici, on_delete=models.CASCADE, related_name='%(class)s')
    num_serie = models.PositiveIntegerField()

    class Meta:
        abstract = True
        unique_together = ('exercici', 'num_serie')

    def __str__(self):
        return f"Sèrie {self.num_serie} de {self.exercici.nom}"


class Forca(Serie):
    grup_muscular = models.CharField(max_length=100)
    pes = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    rpe = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])

    def __str__(self):
        return super().__str__() + " (Força)"


class Resistencia(Serie):
    duracio = models.DurationField()
    tipus_superficie = models.CharField(max_length=10, choices=TipusSuperficie.choices)
    distancia = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    desnivell = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    freq_cardiaca_mitjana = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(30), MaxValueValidator(220)])

    def __str__(self):
        return super().__str__() + " (Resistència)"


class Lesio(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lesions')
    data_inici = models.DateField()
    data_fi = models.DateField(null=True, blank=True)
    zona_afectada = models.CharField(max_length=100)
    grau_serietat = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    estat_actual = models.CharField(max_length=15, choices=EstatActual.choices)
    comentaris_diagnostic = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Lesió {self.zona_afectada} ({self.atleta.nom})"


class Descans(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='descansos')
    data_inici = models.DateTimeField()
    duracio = models.PositiveIntegerField(help_text="En minuts")
    despert = models.PositiveIntegerField()
    rem = models.PositiveIntegerField()
    core = models.PositiveIntegerField()
    deep = models.PositiveIntegerField()
    hrv = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])

    class Meta:
        unique_together = ('atleta', 'data_inici')

    def __str__(self):
        return f"Descans de {self.atleta.nom} ({self.data_inici})"


class RegistreDiari(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='registres_diaris')
    data = models.DateField()
    adaptabilitat_alimentacio = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    comentaris_entrenaments = models.TextField(null=True, blank=True)
    estat_recuperacio_descans = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    nivell_energia = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    nivell_estres = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    sensacions_generals = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('atleta', 'data')

    def __str__(self):
        return f"Registre {self.data} - {self.atleta.nom}"


class InformeIA(models.Model):
    registre_diari = models.OneToOneField(RegistreDiari, on_delete=models.CASCADE, related_name='informe_ia', primary_key=True)
    recomanacio_entrenament = models.TextField()
    recomanacio_alimentacio = models.TextField()
    recomanacio_descans = models.TextField()

    def __str__(self):
        return f"Informe IA per {self.registre_diari}"
