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

# Constants per defecte (es poden reduir amb --fast)
NUM_ATLETES = 12500
NUM_UBICACIONS = 12000
NUM_SESSIONS = 1000000  # Reduït de 8M a 1M per seguretat/rendiment a Ubiwan
NUM_EXERCICIS = 200000
NUM_LESIONS = 6000
NUM_REGISTRES = 1000000  # Reduït per equilibri
NUM_DESCANSOS = 800000
BATCH_SIZE = 10000

OBJECTIUS = [
    'Hyrox', 'Ironman', 'Marató', 'CrossFit', 'Triatló', 'Powerlifting',
    'Ciclisme de Fons', 'Trail Running', 'Halterofília', 'Calistènia', 'Natació'
]
SUPPLEMENTS = [
    'Whey Protein', 'Creatina Monohidratada', 'BCAA 2:1:1', 'Omega 3',
    'Multivitamínic', 'Beta-Alanina', 'L-Glutamina', 'Proteïna Vegana', 'Magnesi'
]
LESIO_ZONES = [
    'Genoll', 'Espatlla', 'Turmell', 'Lumbars', 'Columna', 'Cervicals',
    'Isquiotibials', 'Bessons', 'Colze', 'Poignet'
]
LESIO_COMMENTS = [
    'Seguiment mèdic regular i fisioteràpia.',
    'Rehabilitació activa amb exercicis de mobilitat.',
    "Sensible a l'activitat intensa, cal evitar sobrecàrregues.",
    'Incomoditat al final del dia, repòs preventiu.',
    'Inflamació local, tractament amb gel i antiinflamatoris.',
    'Dolor punxant durant la flexió, sota observació.',
    'Contractura severa, massatge de descàrrega programat.'
]
SESSION_COMMENTS = [
    'Entrenament dur i constant, molt bones sensacions.',
    'Bon ritme, però amb molèsties menors a les articulacions.',
    'Sessió centrada en resistència i control cardiovascular.',
    'Sessió de recuperació adaptada amb volum reduït.',
    'Treball de força màxima excel·lent, nous RPs.',
    'Entrenament en grup, motivació extra.',
    'Molt de vent a la pista exterior, complicat mantenir ritme.',
    'Sessió molt exigent, fatiga muscular acumulada.'
]
VALORACIO_COMMENTS = [
    ('Instal·lacions netes, ben condicionades i material molt nou.', (4.5, 5.0)),
    ('Personal amable però la màquina de rem està espatllada.', (3.0, 4.0)),
    ('La pista exterior és molt còmoda i el terra està en bon estat.', (4.0, 5.0)),
    ('Espai massa concorregut en hora punta, difícil de treballar bé.', (2.0, 3.5)),
    ('Bona ventilació però falta il·luminació en el gimnàs interior.', (3.0, 4.0)),
    ('Material molt bé, però cal més neteja al vestuari de sota.', (3.0, 4.0)),
    ('Molt bona ubicació, facilitat d’aparcament i servei ràpid.', (4.0, 5.0)),
    ("Paviment irregular a la pista d'entrenament exterior, perillós.", (1.5, 3.0)),
    ('Els pesats estan ben organitzats i és fàcil de usar.', (4.0, 5.0)),
    ("L'ambient és massa sorollós, música de fons massa forta.", (2.0, 3.5)),
    ("Excel·lents instal·lacions, ampli espai per a mobilitat i estiraments.", (4.5, 5.0)),
    ("Manca de discos de 20kg en hores punta, cues per a les barres.", (2.5, 3.5))
]
DIARI_COMMENTS = [
    "Sensació d'energia elevada, molt enfocat avui.",
    "Molts dolors musculars (agulletes) després de la sessió de ahir.",
    'Descans insuficient, cal millorar les hores de son.',
    'Alimentació correcta, bona digestió durant el dia.',
    'Lleugera fatiga mental, estrès per exàmens.',
    'Estat d’ànim excel·lent, sense molèsties físiques importants.',
    'Molta set al final del dia, cal millorar la hidratació.'
]
RECOMMENDATIONS = [
    "Ajusta el volum d'entrenament d'aquesta setmana per evitar sobrefatiga.",
    "Reforça l'alimentació con més proteïna i carbohidrats complexos.",
    'Prioritza un son reparador, evita pantalles 1 hora abans de dormir.',
    "Redueix l'estrès general i mantén la hidratació per sobre de 2.5L.",
    "Incrementa el consum de greixos saludables com alvocat i fruits secs.",
    "Redueix la intensitat dels entrenaments de força, enfoca’t en la tècnica.",
    "Bona recuperació. Pots mantenir el pla d'entrenament actual."
]

class Command(BaseCommand):
    help = 'Genera dades massives y coherents per a GoUp AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Genera una fracció petita de les dades per a proves ràpides (ideal per desenvolupament)'
        )

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
        global NUM_ATLETES, NUM_UBICACIONS, NUM_SESSIONS, NUM_EXERCICIS, NUM_LESIONS, NUM_REGISTRES, NUM_DESCANSOS, BATCH_SIZE

        if options['fast']:
            self.stdout.write(self.style.WARNING('MODALITAT FAST ACTIVA: Reduint volum de dades.'))
            NUM_ATLETES = 300
            NUM_UBICACIONS = 150
            NUM_SESSIONS = 5000
            NUM_EXERCICIS = 1500
            NUM_LESIONS = 150
            NUM_REGISTRES = 10000
            NUM_DESCANSOS = 8000
            BATCH_SIZE = 1000

        self.stdout.write(self.style.SUCCESS('Iniciant generació de dades massives...'))
        with transaction.atomic():
            self.flush_tables()

        # Generar Atletes, Alimentació i Ubicacions
        self.generate_atletes_i_alimentacio()
        self.generate_ubicacions()

        self.stdout.write('Obtenint llistats per relacionar...')
        dnis = list(Atleta.objects.values_list('dni_atleta', flat=True))
        if not dnis:
            self.stderr.write("No s'han pogut generar els atletes!")
            return

        ubicacions_ids = list(Ubicacio.objects.values_list('id', flat=True))

        # 1. Generar Exercicis i Series (primer, per poder enllaçar-los en Sessions)
        self.generate_exercicis_i_series(dnis)

        # 2. Generar Lesions (amb id_lesio secuencial per atleta)
        self.generate_lesions(dnis)

        # 3. Generar Sessions, associar exercicis d'atleta i crear valoracions
        self.generate_sessions(dnis, ubicacions_ids)

        # 4. Generar Registres Diaris, Descansos i Informes IA
        self.generate_registres_descans_informes(dnis)

        self.stdout.write(self.style.SUCCESS('\nProcés completat! Dades generades i inserides.'))

    def generate_atletes_i_alimentacio(self):
        self.stdout.write('\n--- Generant Atletes i Alimentació ---')
        atletes_batch = []
        alim_batch = []

        for i in range(1, NUM_ATLETES + 1):
            dni = f"{i:08d}{chr(65 + (i % 26))}"
            atleta = Atleta(
                dni_atleta=dni,
                nom=f"Atleta {i} - {fake.name()}",
                data_naixement=fake.date_of_birth(minimum_age=18, maximum_age=60),
                correu=f"atleta{i}_{random.randint(100,999)}@example.com",
                numero_telefon=f"+346{600000000 + i:09d}",
                pes=round(random.uniform(52.0, 108.0), 2),
                composicio_corporal=f"{round(random.uniform(6.0, 28.0), 1)}% greix",
                altura=round(random.uniform(1.52, 2.05), 2),
                objectiu=random.choice(OBJECTIUS),
                activitat_fisica_diaria=random.choice(ActivitatFisicaDiaria.values),
                estat=random.choice(EstatAtleta.values)
            )
            atletes_batch.append(atleta)

            alim = Alimentacio(
                atleta_id=dni,
                tipus_alimentacio=random.choice(TipusAlimentacio.values),
                calories=round(random.uniform(1600, 3800), 2),
                proteina=round(random.uniform(85, 230), 2),
                carbohidrats=round(random.uniform(120, 380), 2),
                grases=round(random.uniform(45, 115), 2),
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
        ciutat_choices = ['Barcelona', 'València', 'Madrid', 'Girona', 'Sabadell', 'Terrassa', 'Tarragona', 'Lleida']

        for i in range(1, NUM_UBICACIONS + 1):
            ub = Ubicacio(
                tipus_ubicacio=random.choice(TipusUbicacio.values),
                adreca=f"Carrer {fake.street_name()}, {random.randint(1, 450)}, {random.choice(ciutat_choices)}"
            )
            ub_batch.append(ub)
            if i % BATCH_SIZE == 0 or i == NUM_UBICACIONS:
                Ubicacio.objects.bulk_create(ub_batch, ignore_conflicts=True)
                ub_batch = []
                self.print_progress(i, NUM_UBICACIONS, 'Ubicacions')

        self.stdout.write(self.style.SUCCESS('Ubicacions creades.'))

    def generate_exercicis_i_series(self, dnis):
        self.stdout.write('\n--- Generant Exercicis i Sèries ---')
        ex_batch = []
        forca_batch = []
        resistencia_batch = []
        
        # Mapeig de catàleg per enllaçar ràpidament
        self.atleta_exercicis = {dni: [] for dni in dnis}

        # Garantir que tots els atletes tenen almenys 10 exercicis diferents
        atleta_assignments = []
        for dni in dnis:
            atleta_assignments.extend([dni] * 10)
        
        remaining = NUM_EXERCICIS - len(atleta_assignments)
        if remaining > 0:
            atleta_assignments.extend(random.choices(dnis, k=remaining))
        else:
            atleta_assignments = atleta_assignments[:NUM_EXERCICIS]
        
        random.shuffle(atleta_assignments)

        for i in range(1, NUM_EXERCICIS + 1):
            dni = atleta_assignments[i - 1]
            ex_batch.append(Exercici(
                id=i,
                atleta_id=dni,
                nom=f"{fake.word().capitalize()} {random.choice(['Press', 'Squat', 'Run', 'Row', 'Lunge', 'Deadlift', 'Clean', 'Plank'])}",
                descripcio=f"Exercici enfocat en millorar la força o resistència general de l'atleta.",
                descans_entre_series=timedelta(seconds=random.randint(30, 180))
            ))
            self.atleta_exercicis[dni].append(i)

            num_series = random.randint(1, 5)
            is_forca = random.choice([True, False])
            for num_s in range(1, num_series + 1):
                if is_forca:
                    forca_batch.append(Forca(
                        exercici_id=i,
                        num_serie=num_s,
                        grup_muscular=random.choice(['Pectoral', 'Dorsal', 'Cames', 'Esppatlles', 'Core', 'Bíceps/Tríceps']),
                        pes=round(random.uniform(5.0, 160.0), 2),
                        rpe=random.randint(5, 10)
                    ))
                else:
                    resistencia_batch.append(Resistencia(
                        exercici_id=i,
                        num_serie=num_s,
                        duracio=timedelta(minutes=random.randint(5, 60)),
                        tipus_superficie=random.choice(TipusSuperficie.values),
                        distancia=round(random.uniform(1.0, 22.0), 2),
                        desnivell=round(random.uniform(0.0, 600.0), 2) if random.random() > 0.5 else None,
                        freq_cardiaca_mitjana=round(random.uniform(115.0, 185.0), 1)
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

    def generate_lesions(self, dnis):
        self.stdout.write('\n--- Generant Lesions ---')
        lesions_batch = []
        lesions_per_atleta = {}

        for i in range(1, NUM_LESIONS + 1):
            dni = random.choice(dnis)
            lesions_per_atleta[dni] = lesions_per_atleta.get(dni, 0) + 1
            id_les = lesions_per_atleta[dni]

            d_inici = self.random_date_in_past_years(5)
            estat = random.choice(EstatActual.values)
            d_fi = d_inici + timedelta(days=random.randint(7, 180)) if estat == EstatActual.RESOLTA else None

            lesio = Lesio(
                atleta_id=dni,
                id_lesio=id_les,
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
        self.stdout.write('\n--- Generant Sessions ---')
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

            # Generació de valoracions: un atleta té un 30% de probabilitats de valorar
            # un lloc on ha entrenat. Això ens assegura valoracions coherents en volum.
            if random.random() < 0.3:
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
                self.print_progress(i, NUM_SESSIONS, 'Sessions y Valoracions')

        self.stdout.write(self.style.SUCCESS('Sessions y Valoracions creades.'))

        # Enllaçar sessions i exercicis de forma coherent (exercicis de l'atleta que fa la sessió)
        self.stdout.write('\nAssignant exercicis a sessions (taula intermèdia)...')
        ThroughModel = SessioEntrenament.exercicis.through
        through_batch = []
        
        # Anem a recórrer les sessions generades i els hi assignem exercicis
        for sessio_id in range(1, NUM_SESSIONS + 1):
            # No podem fer querys repetides pel rendiment. Per sort, podem deduir
            # l'atleta associat a la sessió si sabem la distribució o si en generem
            # d'una forma predictible. Com que es va fer random.choice, farem una
            # simulació repetible usant la mateixa llavor o, molt més fàcil i
            # ràpid, assignar exercicis basant-nos en el dni de les sessions guardades.
            # Però per evitar querys a base de dades que anirien lentes amb 1M de files:
            # Com que necessitem saber l'atleta de cada sessió, podem guardar en memòria
            # un array d'atleta_ids de sessions mentre es generen!
            # Farem això modificant el generate_sessions per emmagatzemar sessio_atletes.
            pass

    # Per fer-ho correctament, refactoritzem generate_sessions per dur a terme
    # l'assignació directament al final, aprofitant que tenim les dades en memòria.
    # Modifiquem per complet el mètode de generació de sessions.

    def generate_sessions(self, dnis, ubicacions_ids):
        self.stdout.write('\n--- Generant Sessions y Valoracions (M2M Coherent) ---')
        sessions_batch = []
        vals_batch = []
        through_batch = []
        valoracio_pairs = set()
        ThroughModel = SessioEntrenament.exercicis.through

        # Per controlar la barra de progrés dels inserts de M2M
        m2m_total = 0

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

            # Valoració real
            if random.random() < 0.25:
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

            # Assignar exercicis de l'atleta a la sessió (entre 2 i 5 exercicis)
            exs = self.atleta_exercicis.get(dni, [])
            if exs:
                k = min(len(exs), random.randint(2, 5))
                chosen_exs = random.sample(exs, k)
                for ex_id in chosen_exs:
                    through_batch.append(ThroughModel(
                        sessioentrenament_id=i,
                        exercici_id=ex_id
                    ))

            if i % BATCH_SIZE == 0 or i == NUM_SESSIONS:
                SessioEntrenament.objects.bulk_create(sessions_batch, ignore_conflicts=True)
                if vals_batch:
                    Valoracio.objects.bulk_create(vals_batch, ignore_conflicts=True)
                if through_batch:
                    ThroughModel.objects.bulk_create(through_batch, ignore_conflicts=True)
                    m2m_total += len(through_batch)
                
                sessions_batch = []
                vals_batch = []
                through_batch = []
                self.print_progress(i, NUM_SESSIONS, 'Sessions, Valoracions i Relacions M2M')

        self.stdout.write(self.style.SUCCESS(f'\nSessions, {len(valoracio_pairs)} Valoracions i {m2m_total} relacions Sessió-Exercici creades.'))

    def generate_registres_descans_informes(self, dnis):
        self.stdout.write('\n--- Generant Registres Diaris ---')
        date_options = self.build_date_range(5)  # Reduït a 5 anys històrics per volum
        per_atleta_reg = NUM_REGISTRES // len(dnis)
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
                    adaptabilitat_alimentacio=round(random.uniform(25.0, 100.0), 2),
                    comentaris_entrenaments=random.choice(DIARI_COMMENTS),
                    estat_recuperacio_descans=round(random.uniform(1.0, 5.0), 1),
                    nivell_energia=round(random.uniform(1.0, 5.0), 1),
                    nivell_estres=round(random.uniform(0.0, 5.0), 1),
                    sensacions_generals=random.choice(DIARI_COMMENTS)
                ))

                if len(reg_batch) >= BATCH_SIZE:
                    RegistreDiari.objects.bulk_create(reg_batch, ignore_conflicts=True)
                    reg_batch = []
                    self.print_progress(count, NUM_REGISTRES, 'Registres Diaris')

        if reg_batch:
            RegistreDiari.objects.bulk_create(reg_batch, ignore_conflicts=True)
            self.print_progress(count, NUM_REGISTRES, 'Registres Diaris')

        self.stdout.write(self.style.SUCCESS('Registres Diaris creats.'))

        # Generar Informes IA
        self.stdout.write('\n--- Generant Informes IA ---')
        inf_batch = []
        total_informes = RegistreDiari.objects.count()
        inf_count = 0

        # Llegim els IDs de RegistreDiari guardats per evitar violacions de FK
        offset = 0
        CHUNK = 50000

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

        # Generar Descansos
        self.stdout.write('\n--- Generant Descansos ---')
        per_atleta_desc = NUM_DESCANSOS // len(dnis)
        per_atleta_desc = min(per_atleta_desc, len(date_options))

        desc_batch = []
        desc_count = 0

        for dni in dnis:
            selected_dates = random.sample(date_options, per_atleta_desc)
            for data_reg in selected_dates:
                desc_count += 1

                # Minut aleatori d'anar a dormir
                minute = random.randint(22 * 60, 23 * 60 + 59)
                h, m = divmod(minute, 60)
                d_inici_descans = timezone.make_aware(
                    datetime.combine(data_reg - timedelta(days=1), time(hour=h, minute=m))
                )

                duracio_min = random.randint(300, 600)
                despert = random.randint(5, 40)
                rem = int(duracio_min * 0.22)
                deep = int(duracio_min * 0.18)
                core = duracio_min - (despert + rem + deep)

                desc_batch.append(Descans(
                    atleta_id=dni,
                    data_inici=d_inici_descans,
                    duracio=duracio_min,
                    despert=despert,
                    rem=rem,
                    core=core,
                    deep=deep,
                    hrv=round(random.uniform(25.0, 110.0), 2)
                ))

                if len(desc_batch) >= BATCH_SIZE:
                    Descans.objects.bulk_create(desc_batch, ignore_conflicts=True)
                    desc_batch = []
                    self.print_progress(desc_count, NUM_DESCANSOS, 'Descansos')

        if desc_batch:
            Descans.objects.bulk_create(desc_batch, ignore_conflicts=True)
            self.print_progress(desc_count, NUM_DESCANSOS, 'Descansos')

        self.stdout.write(self.style.SUCCESS('Descansos creats.'))