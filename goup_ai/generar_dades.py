import sys
import random
from datetime import timedelta, time, datetime, date
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from faker import Faker

from core.models import (
    Atleta, Alimentacio, Ubicacio, Valoracio, Exercici,
    SessioEntrenament, Forca, Resistencia, Lesio,
    Descans, RegistreDiari, InformeIA,
    ActivitatFisicaDiaria, EstatAtleta, TipusUbicacio,
    TipusAlimentacio, EstatActual, TipusSuperficie
)

fake = Faker('es_ES')

NUM_ATLETES = 12500
NUM_UBICACIONS = 12000
NUM_SESSIONS = 8000000
NUM_EXERCICIS = 200000
NUM_LESIONS = 6000
NUM_REGISTRES = 11000000
NUM_DESCANSOS = 6000000
BATCH_SIZE = 10000

OBJECTIUS = ['Hyrox', 'Ironman', 'Marató', 'CrossFit', 'Triatló', 'Powerlifting']
SUPPLEMENTS = ['Whey', 'Creatina', 'BCAA', None, 'Omega 3', 'Multivitamínic']
LESIO_ZONES = ['Genoll', 'Espatlla', 'Turmell', 'Lumbars', 'Columna', 'Cervicals']
LESIO_COMMENTS = [
    'Seguiment mèdic regular',
    'Rehabilitació en curs',
    "Sensible a l'activitat intensa",
    None
]
SESSION_COMMENTS = [
    'Entrenament dur i constant',
    'Bon ritme, però amb molèsties menors',
    'Sessió centrada en resistència',
    'Sessió de recuperació adaptada',
    None
]
VALORACIO_COMMENTS = [
    ('Instal·lacions netes i ben condicionades.', (4.0, 5.0)),
    ('Personal amable però la màquina de rem està espatllada.', (3.0, 4.0)),
    ('La pista exterior és molt còmoda i el terra està en bon estat.', (4.0, 5.0)),
    ('Espai massa concorregut en hora punta, difícil de treballar bé.', (2.5, 3.5)),
    ('Bona ventilació però falta il·luminació en el gimnàs interior.', (3.0, 4.0)),
    ('Material molt bé, però cal més neteja al vestuari.', (3.0, 4.0)),
    ('Molt bona ubicació i servei ràpid.', (4.0, 5.0)),
    ("Paviment irregular a la pista d'entrenament exterior.", (2.0, 3.5)),
    ('Els pesats estan ben organitzats i fàcils de usar.', (4.0, 5.0)),
    ("L'ambient és massa sorollós per a una pràctica còmoda.", (2.0, 3.0)),
]
DIARI_COMMENTS = [
    "Sensació d'energia elevada",
    "Molts dolors musculars després de l'entrenament",
    'Descans insuficient, cal millorar',
    None
]
RECOMMENDATIONS = [
    "Ajusta el volum d'entrenament.",
    "Reforça l'alimentació amb més proteïna.",
    'Prioritza son reparador.',
    "Redueix l'estrès i mantén la hidratació.",
]

class Command(BaseCommand):
    help = 'Genera dades massives per a la base de dades utilitzant Faker'

    def print_progress(self, current, total, name, action='Generant'):
        percent = (current / total) * 100 if total else 100
        sys.stdout.write(f"\r{action} {name}: {current}/{total} ({percent:.1f}%)")
        sys.stdout.flush()
        if current == total:
            self.stdout.write("")

    def flush_tables(self):
        self.stdout.write('\n--- Eliminant dades antigues ---')
        models = [
            InformeIA, RegistreDiari, Descans,
            SessioEntrenament, Valoracio,
            Forca, Resistencia, Exercici,
            Lesio, Alimentacio, Ubicacio, Atleta
        ]
        for model in models:
            count = model.objects.count()
            self.stdout.write(f"  {model._meta.db_table}: {count}")

        table_names = ', '.join(model._meta.db_table for model in models)
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")

        self.stdout.write(self.style.SUCCESS('Dades antigues eliminades i identitats reiniciades.'))

    def random_date_in_past_years(self, years):
        return date.today() - timedelta(days=random.randint(0, years * 365))

    def build_date_range(self, years=10):
        end = date.today()
        start = end - timedelta(days=years * 365)
        return [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciant generació de dades massives...'))
        with transaction.atomic():
            self.flush_tables()

        self.generate_atletes_i_alimentacio()
        self.generate_ubicacions()

        self.stdout.write('Obtenint llistat de DNI per relacionar dades...')
        dnis = list(Atleta.objects.values_list('dni_atleta', flat=True))
        if not dnis:
            self.stderr.write("No s'han pogut generar els atletes!")
            return

        ubicacions_ids = list(Ubicacio.objects.values_list('id', flat=True))

        self.generate_lesions(dnis)
        self.generate_sessions(dnis, ubicacions_ids)
        self.generate_exercicis_i_series(dnis)
        self.generate_registres_descans_informes(dnis)

        self.stdout.write(self.style.SUCCESS('\nProcés completat! Dades generades i inserides a PostgreSQL.'))

    def generate_atletes_i_alimentacio(self):
        self.stdout.write('\n--- Generant Atletes i Alimentació ---')
        atletes_batch = []
        alim_batch = []

        for i in range(1, NUM_ATLETES + 1):
            dni = f"{i:08d}{chr(65 + (i % 26))}"
            atleta = Atleta(
                dni_atleta=dni,
                nom=f"Atleta {i}",
                data_naixement=fake.date_of_birth(minimum_age=18, maximum_age=60),
                correu=f"atleta{i}@example.com",
                numero_telefon=f"+346{600000000 + i:09d}",
                pes=round(random.uniform(50.0, 110.0), 2),
                composicio_corporal=f"{round(random.uniform(5.0, 30.0), 1)}% Greix",
                altura=round(random.uniform(1.50, 2.10), 2),
                objectiu=random.choice(OBJECTIUS),
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
                suplementacio=random.choice(SUPPLEMENTS)
            )
            alim_batch.append(alim)

            if i % BATCH_SIZE == 0 or i == NUM_ATLETES:
                Atleta.objects.bulk_create(atletes_batch, ignore_conflicts=True)
                Alimentacio.objects.bulk_create(alim_batch, ignore_conflicts=True)
                atletes_batch = []
                alim_batch = []
                self.print_progress(i, NUM_ATLETES, 'Atletes i Alimentació')

        self.stdout.write(self.style.SUCCESS('Atletes i Alimentació creats.'))

    def generate_ubicacions(self):
        self.stdout.write('\n--- Generant Ubicacions ---')
        ub_batch = []
        ciutat_choices = ['Barcelona', 'València', 'Madrid', 'Girona', 'Sabadell', 'Terrassa']

        for i in range(1, NUM_UBICACIONS + 1):
            ub = Ubicacio(
                tipus_ubicacio=random.choice(TipusUbicacio.values),
                adreca=f"Carrer {random.randint(1, 999)}, {random.choice(ciutat_choices)}"
            )
            ub_batch.append(ub)
            if i % BATCH_SIZE == 0 or i == NUM_UBICACIONS:
                Ubicacio.objects.bulk_create(ub_batch, ignore_conflicts=True)
                ub_batch = []
                self.print_progress(i, NUM_UBICACIONS, 'Ubicacions')

        self.stdout.write(self.style.SUCCESS('Ubicacions creades.'))

    def generate_lesions(self, dnis):
        self.stdout.write('\n--- Generant Lesions ---')
        lesions_batch = []

        for i in range(1, NUM_LESIONS + 1):
            d_inici = self.random_date_in_past_years(5)
            estat = random.choice(EstatActual.values)
            d_fi = d_inici + timedelta(days=random.randint(7, 180)) if estat == EstatActual.RESOLTA else None

            lesio = Lesio(
                atleta_id=random.choice(dnis),
                data_inici=d_inici,
                data_fi=d_fi,
                zona_afectada=random.choice(LESIO_ZONES),
                grau_serietat=random.randint(0, 5),
                estat_actual=estat,
                comentaris_diagnostic=random.choice(LESIO_COMMENTS)
            )
            lesions_batch.append(lesio)
            if i % BATCH_SIZE == 0 or i == NUM_LESIONS:
                Lesio.objects.bulk_create(lesions_batch, ignore_conflicts=True)
                lesions_batch = []
                self.print_progress(i, NUM_LESIONS, 'Lesions')

        self.stdout.write(self.style.SUCCESS('Lesions creades.'))

    def generate_sessions(self, dnis, ubicacions_ids):
        self.stdout.write('\n--- Generant Sessions i Valoracions ---')
        sessions_batch = []
        vals_batch = []
        valoracio_pairs = set()

        for i in range(1, NUM_SESSIONS + 1):
            dni = random.choice(dnis)
            ub_id = random.choice(ubicacions_ids)
            data_sessio = self.random_date_in_past_years(2)

            sessions_batch.append(SessioEntrenament(
                id=i,
                atleta_id=dni,
                ubicacio_id=ub_id,
                data=data_sessio,
                duracio_total=timedelta(minutes=random.randint(30, 180)),
                comentaris=random.choice(SESSION_COMMENTS)
            ))

            if random.random() < 0.6:
                key = (dni, ub_id)
                if key not in valoracio_pairs:
                    valoracio_pairs.add(key)
                    comment, rating_range = random.choice(VALORACIO_COMMENTS)
                    vals_batch.append(Valoracio(
                        atleta_id=dni,
                        ubicacio_id=ub_id,
                        valoracio=round(random.uniform(*rating_range), 1),
                        comentaris=comment
                    ))

            if i % BATCH_SIZE == 0 or i == NUM_SESSIONS:
                SessioEntrenament.objects.bulk_create(sessions_batch, ignore_conflicts=True)
                if vals_batch:
                    Valoracio.objects.bulk_create(vals_batch, ignore_conflicts=True)
                sessions_batch = []
                vals_batch = []
                self.print_progress(i, NUM_SESSIONS, 'Sessions')

        self.stdout.write(self.style.SUCCESS('Sessions i Valoracions creades.'))

    def generate_exercicis_i_series(self, dnis):
        self.stdout.write('\n--- Generant Exercicis i Sèries ---')
        ex_batch = []
        forca_batch = []
        resistencia_batch = []

        for i in range(1, NUM_EXERCICIS + 1):
            ex_batch.append(Exercici(
                id=i,
                atleta_id=random.choice(dnis),
                nom=f"{fake.word().capitalize()} {random.choice(['Press', 'Squat', 'Run', 'Row', 'Lunge'])}",
                descripcio=random.choice(LESIO_COMMENTS),
                descans_entre_series=timedelta(seconds=random.randint(30, 180))
            ))

            num_series = random.randint(1, 5)
            is_forca = random.choice([True, False])
            for num_s in range(1, num_series + 1):
                if is_forca:
                    forca_batch.append(Forca(
                        exercici_id=i,
                        num_serie=num_s,
                        grup_muscular=random.choice(['Pectoral', 'Dorsal', 'Cama', 'Espatlla']),
                        pes=round(random.uniform(5.0, 150.0), 2),
                        rpe=random.randint(5, 10)
                    ))
                else:
                    resistencia_batch.append(Resistencia(
                        exercici_id=i,
                        num_serie=num_s,
                        duracio=timedelta(minutes=random.randint(5, 60)),
                        tipus_superficie=random.choice(TipusSuperficie.values),
                        distancia=round(random.uniform(1.0, 20.0), 2),
                        desnivell=round(random.uniform(0.0, 500.0), 2) if random.random() > 0.5 else None,
                        freq_cardiaca_mitjana=round(random.uniform(120.0, 180.0), 1)
                    ))

            if i % BATCH_SIZE == 0 or i == NUM_EXERCICIS:
                Exercici.objects.bulk_create(ex_batch, ignore_conflicts=True)
                Forca.objects.bulk_create(forca_batch, ignore_conflicts=True)
                Resistencia.objects.bulk_create(resistencia_batch, ignore_conflicts=True)
                ex_batch = []
                forca_batch = []
                resistencia_batch = []
                self.print_progress(i, NUM_EXERCICIS, 'Exercicis i Sèries')

        self.stdout.write(self.style.SUCCESS('Exercicis i Sèries creades.'))
        self.stdout.write('\nAssignant exercicis a sessions (taula intermèdia)...')

        ThroughModel = SessioEntrenament.exercicis.through
        through_batch = []
        for i in range(1, NUM_EXERCICIS + 1):
            through_batch.append(ThroughModel(sessioentrenament_id=random.randint(1, NUM_SESSIONS), exercici_id=i))
            if len(through_batch) >= BATCH_SIZE:
                ThroughModel.objects.bulk_create(through_batch, ignore_conflicts=True)
                through_batch = []

        if through_batch:
            ThroughModel.objects.bulk_create(through_batch, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('Relacions de sessió-exercici creades.'))

    def generate_registres_descans_informes(self, dnis):
        # ------------------------------------------------------------------ #
        # 1. REGISTRES DIARIS                                                  #
        # ------------------------------------------------------------------ #
        self.stdout.write('\n--- Generant Registres Diaris ---')
        date_options = self.build_date_range(10)
        per_atleta_reg = NUM_REGISTRES // len(dnis)

        # Assegurem que no demanem més dates que les disponibles
        per_atleta_reg = min(per_atleta_reg, len(date_options))

        reg_batch = []
        count = 0

        for dni in dnis:
            selected_dates = random.sample(date_options, per_atleta_reg)
            for data_reg in selected_dates:
                count += 1
                reg_batch.append(RegistreDiari(
                    id=count,
                    atleta_id=dni,
                    data=data_reg,
                    adaptabilitat_alimentacio=round(random.uniform(0.0, 100.0), 2),
                    comentaris_entrenaments=random.choice(DIARI_COMMENTS),
                    estat_recuperacio_descans=round(random.uniform(0.0, 5.0), 1),
                    nivell_energia=round(random.uniform(0.0, 5.0), 1),
                    nivell_estres=round(random.uniform(0.0, 5.0), 1),
                    sensacions_generals=random.choice(DIARI_COMMENTS)
                ))

                if len(reg_batch) >= BATCH_SIZE:
                    RegistreDiari.objects.bulk_create(reg_batch, ignore_conflicts=True)
                    reg_batch = []
                    self.print_progress(count, NUM_REGISTRES, 'Registres Diaris')

        # Últim batch parcial
        if reg_batch:
            RegistreDiari.objects.bulk_create(reg_batch, ignore_conflicts=True)
            self.print_progress(count, NUM_REGISTRES, 'Registres Diaris')

        self.stdout.write(self.style.SUCCESS('Registres Diaris creats.'))

        # ------------------------------------------------------------------ #
        # 2. INFORMES IA                                                       #
        # CLAU: llegim els IDs REALS de la BD per evitar FK violations.        #
        # bulk_create amb ignore_conflicts pot descartar files (p. ex. per     #
        # unique_together), de manera que no tots els IDs 1..N existiran.      #
        # ------------------------------------------------------------------ #
        self.stdout.write('\n--- Llegint IDs reals de RegistreDiari per generar Informes IA ---')
        # Iterem en chunks per no carregar 11M d'IDs en memòria de cop
        CHUNK = 500_000
        offset = 0
        inf_batch = []
        total_informes = RegistreDiari.objects.count()
        inf_count = 0

        self.stdout.write(f'Total RegistreDiari existents: {total_informes}')
        self.stdout.write('\n--- Generant Informes IA ---')

        while True:
            chunk_ids = list(
                RegistreDiari.objects
                .order_by('id')
                .values_list('id', flat=True)[offset:offset + CHUNK]
            )
            if not chunk_ids:
                break

            for reg_id in chunk_ids:
                inf_count += 1
                inf_batch.append(InformeIA(
                    registre_diari_id=reg_id,
                    recomanacio_entrenament=random.choice(RECOMMENDATIONS),
                    recomanacio_alimentacio=random.choice(RECOMMENDATIONS),
                    recomanacio_descans=random.choice(RECOMMENDATIONS)
                ))

                if len(inf_batch) >= BATCH_SIZE:
                    InformeIA.objects.bulk_create(inf_batch, ignore_conflicts=True)
                    inf_batch = []
                    self.print_progress(inf_count, total_informes, 'Informes IA')

            offset += CHUNK

        if inf_batch:
            InformeIA.objects.bulk_create(inf_batch, ignore_conflicts=True)
            self.print_progress(inf_count, total_informes, 'Informes IA')

        self.stdout.write(self.style.SUCCESS('Informes IA creats.'))

        # ------------------------------------------------------------------ #
        # 3. DESCANSOS                                                         #
        # FIX: random.sample(range(120), 480) fallava perquè el rang era més  #
        # petit que la mostra. Ara generem un minut aleatori per cada data     #
        # independentment, sense necessitat de mostra sense reemplaçament.     #
        # ------------------------------------------------------------------ #
        self.stdout.write('\n--- Generant Descansos ---')
        per_atleta_desc = NUM_DESCANSOS // len(dnis)
        per_atleta_desc = min(per_atleta_desc, len(date_options))

        desc_batch = []
        desc_count = 0

        for dni in dnis:
            selected_dates = random.sample(date_options, per_atleta_desc)
            for data_reg in selected_dates:
                desc_count += 1

                # Minut aleatori entre les 22:00 i les 23:59 (hora d'anar a dormir)
                minute = random.randint(22 * 60, 23 * 60 + 59)
                h, m = divmod(minute, 60)
                d_inici_descans = timezone.make_aware(
                    datetime.combine(data_reg - timedelta(days=1), time(hour=h, minute=m))
                )

                duracio_min = random.randint(300, 600)
                despert = random.randint(10, 30)
                rem = int(duracio_min * 0.25)
                deep = int(duracio_min * 0.20)
                # core = tot el que queda per quadrar la suma exacta
                core = duracio_min - (despert + rem + deep)

                desc_batch.append(Descans(
                    atleta_id=dni,
                    data_inici=d_inici_descans,
                    duracio=duracio_min,
                    despert=despert,
                    rem=rem,
                    core=core,
                    deep=deep,
                    hrv=round(random.uniform(30.0, 100.0), 2)
                ))

                if len(desc_batch) >= BATCH_SIZE:
                    Descans.objects.bulk_create(desc_batch, ignore_conflicts=True)
                    desc_batch = []
                    self.print_progress(desc_count, NUM_DESCANSOS, 'Descansos')

        if desc_batch:
            Descans.objects.bulk_create(desc_batch, ignore_conflicts=True)
            self.print_progress(desc_count, NUM_DESCANSOS, 'Descansos')

        self.stdout.write(self.style.SUCCESS('Descansos creats.'))