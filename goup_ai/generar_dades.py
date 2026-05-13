import sys
import random
from datetime import timedelta, time, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from core.models import (
    Atleta, Alimentacio, Ubicacio, Valoracio, Exercici, 
    SessioEntrenament, Serie, Forca, Resistencia, Lesio, 
    Descans, RegistreDiari, InformeIA, 
    ActivitatFisicaDiaria, EstatAtleta, TipusUbicacio, 
    TipusAlimentacio, EstatActual, TipusSuperficie
)

fake = Faker('es_ES')

NUM_ATLETES = 20000
NUM_UBICACIONS = 20000
NUM_SESSIONS = 3000000
NUM_EXERCICIS = 200000
NUM_LESIONS = 35000
NUM_REGISTRES = 5000000 # Registres diaris, informes, descans
BATCH_SIZE = 3000 # Inserció per blocs per no saturar memòria ni xarxa

class Command(BaseCommand):
    help = 'Genera dades massives per a la base de dades utilitzant Faker'

    def print_progress(self, current, total, name):
        percent = (current / total) * 100
        sys.stdout.write(f"\rGenerant {name}: {current}/{total} ({percent:.1f}%)")
        sys.stdout.flush()
        if current == total:
            self.stdout.write("")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Esborrant dades antigues (això pot trigar una mica)..."))
        
        # Eliminar dades (neteja ràpida si ja s'havia executat)
        Atleta.objects.all().delete()
        Ubicacio.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Iniciant generació de dades massives..."))

        self.generate_atletes_i_alimentacio()
        
        self.stdout.write("Obtenint llistat de DNI per relacionar dades...")
        dnis = list(Atleta.objects.values_list('dni_atleta', flat=True))
        if not dnis:
            self.stderr.write("No s'han pogut generar els atletes!")
            return

        self.generate_ubicacions()
        
        ubicacions_ids = list(Ubicacio.objects.values_list('id', flat=True))
        
        self.generate_lesions(dnis)
        self.generate_sessions(dnis, ubicacions_ids)
        self.generate_exercicis_i_series(dnis)
        self.generate_registres_descans_informes(dnis)

        self.stdout.write(self.style.SUCCESS("\nProcés completat! Dades generades i inserides a PostgreSQL."))

    def generate_atletes_i_alimentacio(self):
        self.stdout.write("\n--- Generant Atletes i Alimentació ---")
        atletes_batch = []
        alim_batch = []

        for i in range(1, NUM_ATLETES + 1):
            dni = fake.unique.bothify(text='########?').upper()
            
            atleta = Atleta(
                dni_atleta=dni,
                nom=fake.name(),
                data_naixement=fake.date_of_birth(minimum_age=18, maximum_age=60),
                correu=fake.unique.email(),
                numero_telefon=fake.unique.phone_number()[:20],
                pes=round(random.uniform(50.0, 110.0), 2),
                composicio_corporal=f"{round(random.uniform(5.0, 30.0), 1)}% Greix",
                altura=round(random.uniform(1.50, 2.10), 2),
                objectiu=random.choice(['Hyrox', 'Ironman', 'Marató', 'CrossFit']),
                activitat_fisica_diaria=random.choice(ActivitatFisicaDiaria.values),
                estat=random.choice(EstatAtleta.values)
            )
            atletes_batch.append(atleta)
            
            alim = Alimentacio(
                atleta_id=dni,
                tipus_alimentacio=random.choice(TipusAlimentacio.values),
                calories=round(random.uniform(1500, 4000), 2),
                proteina=round(random.uniform(80, 250), 2),
                carbohidrats=round(random.uniform(100, 400), 2),
                grases=round(random.uniform(40, 120), 2),
                suplementacio=random.choice(["Whey", "Creatina", None])
            )
            alim_batch.append(alim)

            if i % BATCH_SIZE == 0 or i == NUM_ATLETES:
                Atleta.objects.bulk_create(atletes_batch, ignore_conflicts=True)
                Alimentacio.objects.bulk_create(alim_batch, ignore_conflicts=True)
                atletes_batch, alim_batch = [], []
                self.print_progress(i, NUM_ATLETES, "Atletes i Alimentació")

    def generate_ubicacions(self):
        self.stdout.write("\n--- Generant Ubicacions ---")
        ub_batch = []
        for i in range(1, NUM_UBICACIONS + 1):
            ub = Ubicacio(
                tipus_ubicacio=random.choice(TipusUbicacio.values),
                adreca=fake.address().replace('\n', ', ')[:200]
            )
            ub_batch.append(ub)
            if i % BATCH_SIZE == 0 or i == NUM_UBICACIONS:
                Ubicacio.objects.bulk_create(ub_batch, ignore_conflicts=True)
                ub_batch = []
                self.print_progress(i, NUM_UBICACIONS, "Ubicacions")

    def generate_lesions(self, dnis):
        self.stdout.write("\n--- Generant Lesions ---")
        lesions_batch = []
        for i in range(1, NUM_LESIONS + 1):
            d_inici = fake.date_between(start_date='-10y', end_date='today')
            estat = random.choice(EstatActual.values)
            d_fi = d_inici + timedelta(days=random.randint(7, 180)) if estat == EstatActual.RESOLTA else None
            
            lesio = Lesio(
                atleta_id=random.choice(dnis),
                data_inici=d_inici,
                data_fi=d_fi,
                zona_afectada=random.choice(['Genoll', 'Espatlla', 'Turmell', 'Lumbars']),
                grau_serietat=random.randint(0, 5),
                estat_actual=estat,
                comentaris_diagnostic=fake.sentence() if random.random() > 0.5 else None
            )
            lesions_batch.append(lesio)
            if i % BATCH_SIZE == 0 or i == NUM_LESIONS:
                Lesio.objects.bulk_create(lesions_batch, ignore_conflicts=True)
                lesions_batch = []
                self.print_progress(i, NUM_LESIONS, "Lesions")

    def generate_sessions(self, dnis, ubicacions_ids):
        self.stdout.write("\n--- Generant Sessions i Valoracions ---")
        sessions_batch = []
        vals_batch = []
        for i in range(1, NUM_SESSIONS + 1):
            dni = random.choice(dnis)
            ub_id = random.choice(ubicacions_ids)
            data_sessio = fake.date_between(start_date='-10y', end_date='today')
            
            sessio = SessioEntrenament(
                id=i,
                atleta_id=dni,
                ubicacio_id=ub_id,
                data=data_sessio,
                duracio_total=timedelta(minutes=random.randint(30, 180)),
                comentaris=fake.sentence() if random.random() > 0.5 else None
            )
            sessions_batch.append(sessio)
            
            if random.random() < 0.2:
                val = Valoracio(
                    atleta_id=dni,
                    ubicacio_id=ub_id,
                    valoracio=round(random.uniform(0.0, 5.0), 1),
                    comentaris=fake.sentence() if random.random() > 0.3 else None
                )
                vals_batch.append(val)
                
            if i % BATCH_SIZE == 0 or i == NUM_SESSIONS:
                SessioEntrenament.objects.bulk_create(sessions_batch, ignore_conflicts=True)
                Valoracio.objects.bulk_create(vals_batch, ignore_conflicts=True)
                sessions_batch, vals_batch = [], []
                self.print_progress(i, NUM_SESSIONS, "Sessions")

    def generate_exercicis_i_series(self, dnis):
        self.stdout.write("\n--- Generant Exercicis, Relacions i Sèries ---")
        ex_batch = []
        forca_batch = []
        resistencia_batch = []
        
        # Obtenim IDs de sessió reals creats
        sessions_ids = list(SessioEntrenament.objects.values_list('id', flat=True))
        if not sessions_ids:
            return

        for i in range(1, NUM_EXERCICIS + 1):
            ex = Exercici(
                id=i,
                atleta_id=random.choice(dnis),
                nom=fake.word().capitalize() + " " + random.choice(["Press", "Squat", "Run"]),
                descripcio=fake.sentence() if random.random() > 0.5 else None,
                descans_entre_series=timedelta(seconds=random.randint(30, 180))
            )
            ex_batch.append(ex)
            
            num_series = random.randint(1, 5)
            is_forca = random.choice([True, False])
            
            for num_s in range(1, num_series + 1):
                if is_forca:
                    f = Forca(
                        exercici_id=i,
                        num_serie=num_s,
                        grup_muscular=random.choice(["Pectoral", "Dorsal", "Cama"]),
                        pes=round(random.uniform(5.0, 150.0), 2),
                        rpe=random.randint(5, 10)
                    )
                    forca_batch.append(f)
                else:
                    r = Resistencia(
                        exercici_id=i,
                        num_serie=num_s,
                        duracio=timedelta(minutes=random.randint(5, 60)),
                        tipus_superficie=random.choice(TipusSuperficie.values),
                        distancia=round(random.uniform(1.0, 20.0), 2),
                        desnivell=round(random.uniform(0.0, 500.0), 2) if random.random() > 0.5 else None,
                        freq_cardiaca_mitjana=round(random.uniform(120.0, 180.0), 1)
                    )
                    resistencia_batch.append(r)
                    
            if i % BATCH_SIZE == 0 or i == NUM_EXERCICIS:
                Exercici.objects.bulk_create(ex_batch, ignore_conflicts=True)
                Forca.objects.bulk_create(forca_batch, ignore_conflicts=True)
                Resistencia.objects.bulk_create(resistencia_batch, ignore_conflicts=True)
                ex_batch, forca_batch, resistencia_batch = [], [], []
                self.print_progress(i, NUM_EXERCICIS, "Exercicis i Sèries")

        # Ara les relacions sessio_entrenament_exercicis (SessioExercici)
        self.stdout.write("\nAssignant exercicis a sessions (Through table)...")
        # Això ho podem fer afegint entrades directament a la taula intermèdia
        ThroughModel = SessioEntrenament.exercicis.through
        through_batch = []
        for i in range(1, NUM_EXERCICIS + 1):
            sessio_id = random.choice(sessions_ids)
            through_batch.append(ThroughModel(sessioentrenament_id=sessio_id, exercici_id=i))
            if i % (BATCH_SIZE*5) == 0 or i == NUM_EXERCICIS:
                ThroughModel.objects.bulk_create(through_batch, ignore_conflicts=True)
                through_batch = []

    def generate_registres_descans_informes(self, dnis):
        self.stdout.write("\n--- Generant Registres Diaris, Informes i Descans (10 anys) ---")
        
        # Procesamos en bloques pequeños para asegurar la integridad
        BLOQUE_ATLETES = 100 
        
        for i in range(0, len(dnis), BLOQUE_ATLETES):
            batch_dnis = dnis[i:i + BLOQUE_ATLETES]
            
            with transaction.atomic():
                for dni in batch_dnis:
                    reg_batch = []
                    # Generamos una fecha aleatoria en los últimos 10 años para este atleta
                    # Si quieres mucha densidad, podrías hacer un bucle de fechas aquí
                    for _ in range(NUM_REGISTRES // len(dnis)): 
                        data_reg = fake.date_between(start_date='-10y', end_date='today')
                        
                        reg_batch.append(RegistreDiari(
                            atleta_id=dni,
                            data=data_reg,
                            adaptabilitat_alimentacio=round(random.uniform(0.0, 100.0), 2),
                            estat_recuperacio_descans=round(random.uniform(0.0, 5.0), 1),
                            nivell_energia=round(random.uniform(0.0, 5.0), 1),
                            nivell_estres=round(random.uniform(0.0, 5.0), 1)
                        ))
                    
                    # Insertamos los registros de este atleta. 
                    # Usamos ignore_conflicts para saltar fechas repetidas sin romper el script
                    registres_creats = RegistreDiari.objects.bulk_create(reg_batch, ignore_conflicts=True)
                    
                    # Para evitar el error de la FK, vamos a crear Informes y Descansos 
                    # SOLO de los registros que acabamos de insertar y que existen de verdad
                    regs_reals = RegistreDiari.objects.filter(atleta_id=dni).only('id', 'data')
                    
                    desc_batch = []
                    inf_batch = []
                    
                    for r in regs_reals:
                        # Solo creamos informe/descanso si no existen ya (evita errores)
                        # Pero para ir rápido en la simulación, generamos datos aleatorios lligats al ID real
                        inf_batch.append(InformeIA(
                            registre_diari_id=r.id,
                            recomanacio_entrenament=fake.sentence(),
                            recomanacio_alimentacio=fake.sentence(),
                            recomanacio_descans=fake.sentence()
                        ))
                        
                        duracio_min = random.randint(300, 600)
                        desc_batch.append(Descans(
                            atleta_id=dni,
                            data_inici=timezone.make_aware(datetime.combine(r.data, time(23,0))),
                            duracio=duracio_min,
                            despert=20, rem=60, core=200, deep=60,
                            hrv=round(random.uniform(40, 80), 2)
                        ))
                    
                    # Insertamos los hijos. ignore_conflicts aquí evita que falle si ya tenían informe
                    InformeIA.objects.bulk_create(inf_batch, ignore_conflicts=True)
                    Descans.objects.bulk_create(desc_batch, ignore_conflicts=True)
            
            self.print_progress(min(i + BLOQUE_ATLETES, len(dnis)), len(dnis), "Atletes amb registres")