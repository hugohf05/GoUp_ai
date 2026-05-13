import random
from datetime import datetime, timedelta, date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from core.models import (
    Atleta, Alimentacio, Ubicacio, Valoracio, Exercici, 
    SessioEntrenament, Forca, Resistencia, Lesio, 
    Descans, RegistreDiari, InformeIA, 
    EstatAtleta, ActivitatFisicaDiaria, TipusAlimentacio, 
    EstatActual, TipusSuperficie, TipusUbicacio
)

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la BD amb 10 anys de dades coherents'

    def handle(self, *args, **options):
        # --- CONFIGURACIÓ ---
        NUM_ATLETES = 2000  # Atletes amb història profunda
        ANYS_HISTORIA = 10
        BATCH_SIZE = 5000   # Per optimitzar memòria
        
        self.stdout.write(self.style.SUCCESS(f'Iniciant població de 10 anys per a {NUM_ATLETES} atletes...'))

        # 1. Creació d'Ubicacions (Gimnasos, parcs...)
        self.stdout.write('Creant ubicacions...')
        ubicacions = []
        for _ in range(50):
            ubicacions.append(Ubicacio.objects.create(
                tipus_ubicacio=random.choice(TipusUbicacio.choices)[0],
                adreca=fake.address()[:200]
            ))

        # 2. Bucle Principal per Atleta (Per mantenir coherència temporal)
        for i in range(NUM_ATLETES):
            with transaction.atomic(): # Transacció per atleta per seguretat
                # Crear Atleta
                dni = fake.unique.bothify(text='########?').upper()
                data_alta = date.today() - timedelta(days=random.randint(30, 365 * ANYS_HISTORIA))
                
                atleta = Atleta.objects.create(
                    dni_atleta=dni,
                    nom=fake.name(),
                    data_naixement=fake.date_of_birth(minimum_age=18, maximum_age=55),
                    correu=fake.unique.email(),
                    numero_telefon=fake.unique.phone_number()[:20],
                    pes=random.uniform(60, 95),
                    composicio_corporal=f"{random.randint(10,25)}% greix",
                    altura=random.uniform(1.60, 2.00),
                    objectiu=random.choice(['Marató', 'Hipertròfia', 'Salut', 'Hyrox']),
                    activitat_fisica_diaria=random.choice(ActivitatFisicaDiaria.choices)[0],
                    estat=EstatAtleta.ACTIU
                )

                # Alimentació (1 a 1)
                Alimentacio.objects.create(
                    atleta=atleta,
                    tipus_alimentacio=random.choice(TipusAlimentacio.choices)[0],
                    calories=random.randint(2000, 3500),
                    proteina=random.randint(120, 200),
                    carbohidrats=random.randint(200, 400),
                    grases=random.randint(60, 100)
                )

                # Generar Exercicis base de l'atleta (El seu catàleg personal)
                ex_base = []
                for _ in range(5):
                    ex_base.append(Exercici.objects.create(
                        atleta=atleta,
                        nom=fake.word().capitalize() + " " + random.choice(['Press', 'Sèrie', 'Running']),
                        descans_entre_series=timedelta(seconds=random.randint(60, 120))
                    ))

                # --- GENERACIÓ TEMPORAL (Dia a dia) ---
                curr_date = data_alta
                registres_diaris = []
                descansos = []

                while curr_date <= date.today():
                    # A. Descans (Diari)
                    despert, rem, core, deep = random.randint(10,30), random.randint(60,120), random.randint(200,300), random.randint(60,120)
                    duracio_total = despert + rem + core + deep
                    
                    descansos.append(Descans(
                        atleta=atleta,
                        data_inici=datetime.combine(curr_date - timedelta(days=1), datetime.min.time()) + timedelta(hours=22, minutes=random.randint(0,60)),
                        duracio=duracio_total,
                        despert=despert, rem=rem, core=core, deep=deep,
                        hrv=random.uniform(40, 80)
                    ))

                    # B. Registre Diari (Cada dia)
                    reg = RegistreDiari(
                        atleta=atleta,
                        data=curr_date, # Nota: En el model tens auto_now_add, però aquí forcem la data històrica
                        adaptabilitat_alimentacio=random.uniform(70, 100),
                        estat_recuperacio_descans=random.uniform(2, 5),
                        nivell_energia=random.uniform(2, 5),
                        nivell_estres=random.uniform(1, 4),
                    )
                    registres_diaris.append(reg)

                    # C. Sessions d'entrenament (3 cops per setmana)
                    if curr_date.weekday() in [0, 2, 4]:
                        sessio = SessioEntrenament.objects.create(
                            atleta=atleta,
                            ubicacio=random.choice(ubicacions),
                            data=curr_date,
                            duracio_total=timedelta(minutes=random.randint(45, 90)),
                        )
                        sessio.exercicis.add(random.choice(ex_base))

                    curr_date += timedelta(days=1)

                # Inserció massiva de l'atleta actual
                Descans.objects.bulk_create(descansos)
                # Nota: RegistreDiari té un mètode clean i data auto_now_add. 
                # Per inserir històric, hem de fer-ho via SQL o canviar temporalment el model.
                # Aquí fem un save estàndard per respectar el model:
                for r in registres_diaris:
                    # Sobreescribim la data manualment per l'històric
                    r.save()
                    # Assignem data manual després del save perquè auto_now_add la trepitja
                    RegistreDiari.objects.filter(pk=r.pk).update(data=r.data)
                    
                    # Informe IA (1 a 1 amb registre)
                    InformeIA.objects.create(
                        registre_diari=r,
                        recomanacio_entrenament="Seguiu així",
                        recomanacio_alimentacio="Mantingueu proteïna",
                        recomanacio_descans="Dormiu 8h"
                    )

            if i % 10 == 0:
                self.stdout.write(f'Processats {i}/{NUM_ATLETES} atletes...')

        self.stdout.write(self.style.SUCCESS('Població finalitzada amb èxit!'))