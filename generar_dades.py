#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import psycopg2.extras
import random
import datetime
import sys
from faker import Faker

fake = Faker('es_ES')

# ==============================================================================
# CONFIGURACIÓ DE CONNEXIÓ A UBIWAN
# ==============================================================================
DB_HOST = "localhost" # 'localhost' si ho executes directament a dins d'ubiwan, sinó l'IP d'ubiwan
DB_USER = "est_e7864955"
DB_PASS = "dB.e7864955"
DB_NAME = "est_e7864955"
SCHEMA  = "practica"

# ==============================================================================
# CONFIGURACIÓ DEL VOLUM DE DADES
# ==============================================================================
# "Centenars de milers"
NUM_ATLETES = 100000
NUM_UBICACIONS = 5000
NUM_SESSIONS = 300000
NUM_EXERCICIS = 400000
NUM_LESIONS = 20000
NUM_REGISTRES = 200000 # Registres diaris, informes, descans
BATCH_SIZE = 5000 # Inserció per blocs per no saturar memòria ni xarxa

# ==============================================================================
# LLISTES DE SUPORT (DOMINIS)
# ==============================================================================
estat_atleta_choices = ['ACTIU', 'LESIONAT']
activitat_choices = ['SEDENTARI', 'ACTIU', 'MOLT_ACTIU']
tipus_ubicacio_choices = ['EXTERIOR', 'INTERIOR']
estat_lesio_choices = ['ACTIVA', 'REHABILITACIO', 'RESOLTA']
alimentacio_choices = ['VEGETARIA', 'VEGA', 'OMNIVOR']
superficie_choices = ['ASFALT', 'CINTA', 'TRAIL']
objectius_choices = ['Hyrox', 'Ironman', 'Marató', 'CrossFit', 'Powerlifting', 'Híbrid 5K', 'Triatló Sprint']
musculs_choices = ['Pectoral', 'Dorsal', 'Cama', 'Espatlla', 'Braç', 'Core']
zones_lesio_choices = ['Genoll dret', 'Genoll esquerre', 'Espatlla dreta', 'Espatlla esquerra', 'Turmell', 'Lumbars', 'Isquiotibials', 'Tendó d\'Aquiles']

def print_progress(current, total, name):
    percent = (current / total) * 100
    sys.stdout.write(f"\rGenerant {name}: {current}/{total} ({percent:.1f}%)")
    sys.stdout.flush()
    if current == total:
        print()

def generate_and_insert_atletes(conn):
    print("\n--- Generant Atletes i Alimentació ---")
    cur = conn.cursor()
    atleta_data = []
    alimentacio_data = []
    
    for i in range(1, NUM_ATLETES + 1):
        dni = fake.unique.bothify(text='########?').upper()
        correu = fake.unique.email()
        telefon = fake.unique.phone_number()[:20] # Truncar per la BD
        
        nom = fake.name()
        data_naix = fake.date_of_birth(minimum_age=18, maximum_age=60)
        pes = round(random.uniform(50.0, 110.0), 2)
        composicio = f"{round(random.uniform(5.0, 30.0), 1)}% Greix"
        altura = round(random.uniform(1.50, 2.10), 2)
        objectiu = random.choice(objectius_choices)
        activitat = random.choice(activitat_choices)
        estat = random.choice(estat_atleta_choices)
        
        atleta_data.append((dni, nom, data_naix, correu, telefon, pes, composicio, altura, objectiu, activitat, estat))
        
        # Generar alimentació per aquest atleta
        t_alimentacio = random.choice(alimentacio_choices)
        calories = round(random.uniform(1500, 4000), 2)
        prot = round(random.uniform(80, 250), 2)
        carb = round(random.uniform(100, 400), 2)
        greix = round(random.uniform(40, 120), 2)
        suple = random.choice(["Proteïna Whey, Creatina", "Creatina, Multivitamínic", "BCAA", None, "Omega 3", "Maltodextrina"])
        
        alimentacio_data.append((dni, t_alimentacio, calories, prot, carb, greix, suple))
        
        if i % BATCH_SIZE == 0 or i == NUM_ATLETES:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO atleta (dni_atleta, nom, data_naixement, correu, numero_telefon, pes, composicio_corporal, altura, objectiu, activitat_fisica_diaria, estat) VALUES %s ON CONFLICT DO NOTHING",
                atleta_data,
                page_size=BATCH_SIZE
            )
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO alimentacio (dni_atleta, tipus_alimentacio, calories, proteina, carbohidrats, grases, suplementacio) VALUES %s ON CONFLICT DO NOTHING",
                alimentacio_data,
                page_size=BATCH_SIZE
            )
            conn.commit()
            atleta_data = []
            alimentacio_data = []
            print_progress(i, NUM_ATLETES, "Atletes i Alimentació")

    cur.close()

def fetch_all_dnis(conn):
    cur = conn.cursor()
    cur.execute("SELECT dni_atleta FROM atleta")
    res = [row[0] for row in cur.fetchall()]
    cur.close()
    return res

def generate_and_insert_ubicacions(conn):
    print("\n--- Generant Ubicacions ---")
    cur = conn.cursor()
    ubicacio_data = []
    
    for i in range(1, NUM_UBICACIONS + 1):
        id_ub = i
        t_ub = random.choice(tipus_ubicacio_choices)
        adreca = fake.address().replace('\n', ', ')[:200]
        ubicacio_data.append((id_ub, t_ub, adreca))
        
        if i % BATCH_SIZE == 0 or i == NUM_UBICACIONS:
            psycopg2.extras.execute_values(cur, "INSERT INTO ubicacio (id_ubicacio, tipus_ubicacio, adreca) VALUES %s ON CONFLICT DO NOTHING", ubicacio_data, page_size=BATCH_SIZE)
            conn.commit()
            ubicacio_data = []
            print_progress(i, NUM_UBICACIONS, "Ubicacions")
    cur.close()

def generate_and_insert_lesions(conn, dnis):
    print("\n--- Generant Lesions ---")
    cur = conn.cursor()
    lesio_data = []
    
    for i in range(1, NUM_LESIONS + 1):
        id_lesio = i
        dni = random.choice(dnis)
        d_inici = fake.date_between(start_date='-5y', end_date='today')
        estat = random.choice(estat_lesio_choices)
        d_fi = None
        if estat == 'RESOLTA':
            d_fi = d_inici + datetime.timedelta(days=random.randint(7, 180))
        
        zona = random.choice(zones_lesio_choices)
        grau = random.randint(0, 5)
        comentaris = fake.sentence() if random.choice([True, False]) else None
        
        lesio_data.append((id_lesio, dni, d_inici, d_fi, zona, grau, estat, comentaris))
        
        if i % BATCH_SIZE == 0 or i == NUM_LESIONS:
            psycopg2.extras.execute_values(cur, "INSERT INTO lesio (id_lesio, dni_atleta, data_inici, data_fi, zona_afectada, grau_serietat, estat_actual, comentaris_diagnostic) VALUES %s ON CONFLICT DO NOTHING", lesio_data, page_size=BATCH_SIZE)
            conn.commit()
            lesio_data = []
            print_progress(i, NUM_LESIONS, "Lesions")
    cur.close()

def generate_and_insert_sessions_and_valoracions(conn, dnis):
    print("\n--- Generant Sessions i Valoracions ---")
    cur = conn.cursor()
    sessio_data = []
    valoracio_data = []
    
    for i in range(1, NUM_SESSIONS + 1):
        id_sessio = i
        dni = random.choice(dnis)
        id_ub = random.randint(1, NUM_UBICACIONS)
        data_sessio = fake.date_between(start_date='-2y', end_date='today')
        duracio_minuts = random.randint(30, 180)
        duracio_interval = f"{duracio_minuts} minutes"
        comentaris = fake.sentence() if random.random() > 0.5 else None
        
        sessio_data.append((id_sessio, dni, id_ub, data_sessio, duracio_interval, comentaris))
        
        if random.random() < 0.2:
            val = round(random.uniform(0.0, 5.0), 1)
            comentari_val = fake.sentence() if random.random() > 0.3 else None
            valoracio_data.append((dni, id_ub, val, comentari_val))
            
        if i % BATCH_SIZE == 0 or i == NUM_SESSIONS:
            psycopg2.extras.execute_values(cur, "INSERT INTO sessio_entrenament (id_sessio, dni_atleta, id_ubicacio, data, duracio_total, comentaris) VALUES %s ON CONFLICT DO NOTHING", sessio_data, page_size=BATCH_SIZE)
            if valoracio_data:
                psycopg2.extras.execute_values(cur, "INSERT INTO valoracio (dni_atleta, id_ubicacio, valoracio, comentaris) VALUES %s ON CONFLICT DO NOTHING", valoracio_data, page_size=BATCH_SIZE)
            
            conn.commit()
            sessio_data = []
            valoracio_data = []
            print_progress(i, NUM_SESSIONS, "Sessions")
    cur.close()

def generate_and_insert_exercicis_and_series(conn, dnis):
    print("\n--- Generant Exercicis i Sèries ---")
    cur = conn.cursor()
    ex_data = []
    sessio_ex_data = []
    serie_data = []
    forca_data = []
    resistencia_data = []
    
    for i in range(1, NUM_EXERCICIS + 1):
        id_ex = i
        dni = random.choice(dnis)
        nom = fake.word().capitalize() + " " + random.choice(["Press", "Curl", "Squat", "Run", "Row", "Lunge"])
        descripcio = fake.sentence() if random.random() > 0.5 else None
        descans = f"{random.randint(30, 180)} seconds"
        ex_data.append((id_ex, dni, nom, descripcio, descans))
        
        sessio_ex_data.append((random.randint(1, NUM_SESSIONS), id_ex))
        
        num_series = random.randint(1, 5)
        is_forca = random.choice([True, False])
        
        for num_s in range(1, num_series + 1):
            serie_data.append((id_ex, num_s))
            if is_forca:
                grup = random.choice(musculs_choices)
                pes = round(random.uniform(5.0, 150.0), 2)
                rpe = random.randint(5, 10)
                forca_data.append((id_ex, num_s, grup, pes, rpe))
            else:
                duracio = f"{random.randint(5, 60)} minutes"
                sup = random.choice(superficie_choices)
                dist = round(random.uniform(1.0, 20.0), 2)
                desnivell = round(random.uniform(0.0, 500.0), 2) if random.random() > 0.5 else None
                fcm = round(random.uniform(120.0, 180.0), 1)
                resistencia_data.append((id_ex, num_s, duracio, sup, dist, desnivell, fcm))
        
        if i % BATCH_SIZE == 0 or i == NUM_EXERCICIS:
            psycopg2.extras.execute_values(cur, "INSERT INTO exercici (id_ex, dni_atleta, nom, descripcio, descans_entre_series) VALUES %s ON CONFLICT DO NOTHING", ex_data, page_size=BATCH_SIZE)
            psycopg2.extras.execute_values(cur, "INSERT INTO sessio_exercici (id_sessio, id_ex) VALUES %s ON CONFLICT DO NOTHING", sessio_ex_data, page_size=BATCH_SIZE)
            psycopg2.extras.execute_values(cur, "INSERT INTO serie (id_ex, num_serie) VALUES %s ON CONFLICT DO NOTHING", serie_data, page_size=BATCH_SIZE)
            if forca_data:
                psycopg2.extras.execute_values(cur, "INSERT INTO forca (id_ex, num_serie, grup_muscular, pes, rpe) VALUES %s ON CONFLICT DO NOTHING", forca_data, page_size=BATCH_SIZE)
            if resistencia_data:
                psycopg2.extras.execute_values(cur, "INSERT INTO resistencia (id_ex, num_serie, duracio, tipus_superficie, distancia, desnivell, freq_cardiaca_mitjana) VALUES %s ON CONFLICT DO NOTHING", resistencia_data, page_size=BATCH_SIZE)
            
            conn.commit()
            ex_data, sessio_ex_data, serie_data, forca_data, resistencia_data = [], [], [], [], []
            print_progress(i, NUM_EXERCICIS, "Exercicis i Sèries")
    cur.close()

def generate_and_insert_registres(conn, dnis):
    print("\n--- Generant Registres Diaris, Informes i Descans ---")
    cur = conn.cursor()
    registre_data = []
    informe_data = []
    descans_data = []
    
    for i in range(1, NUM_REGISTRES + 1):
        dni = random.choice(dnis)
        data_reg = fake.date_between(start_date='-1y', end_date='today')
        
        duracio_minuts = random.randint(300, 600)
        despert = random.randint(10, 30)
        rem = int(duracio_minuts * 0.25)
        deep = int(duracio_minuts * 0.20)
        core = duracio_minuts - (despert + rem + deep)
        hrv = round(random.uniform(30.0, 100.0), 2)
        hora = datetime.time(hour=random.randint(22, 23), minute=random.randint(0, 59))
        data_inici_descans = datetime.datetime.combine(data_reg - datetime.timedelta(days=1), hora)
        
        descans_data.append((dni, data_inici_descans, duracio_minuts, despert, rem, core, deep, hrv))
        
        adapta = round(random.uniform(0.0, 100.0), 2)
        comentari_ent = fake.sentence() if random.random() > 0.5 else None
        recup = round(random.uniform(0.0, 5.0), 1)
        energia = round(random.uniform(0.0, 5.0), 1)
        estres = round(random.uniform(0.0, 5.0), 1)
        sensacions = fake.sentence() if random.random() > 0.5 else None
        
        registre_data.append((dni, data_reg, adapta, comentari_ent, recup, energia, estres, sensacions))
        
        rec_ent = "Recomanació entrenament: " + fake.sentence()
        rec_alim = "Recomanació alimentació: " + fake.sentence()
        rec_desc = "Recomanació descans: " + fake.sentence()
        
        informe_data.append((dni, data_reg, rec_ent, rec_alim, rec_desc))
        
        if i % BATCH_SIZE == 0 or i == NUM_REGISTRES:
            psycopg2.extras.execute_values(cur, "INSERT INTO descans (dni_atleta, data_inici, duracio, despert, rem, core, deep, hrv) VALUES %s ON CONFLICT DO NOTHING", descans_data, page_size=BATCH_SIZE)
            psycopg2.extras.execute_values(cur, "INSERT INTO registre_diari (dni_atleta, data, adaptabilitat_alimentacio, comentaris_entrenaments, estat_recuperacio_descans, nivell_energia, nivell_estres, sensacions_generals) VALUES %s ON CONFLICT DO NOTHING", registre_data, page_size=BATCH_SIZE)
            psycopg2.extras.execute_values(cur, "INSERT INTO informe_ia (dni_atleta, data, recomanacio_entrenament, recomanacio_alimentacio, recomanacio_descans) VALUES %s ON CONFLICT DO NOTHING", informe_data, page_size=BATCH_SIZE)
            conn.commit()
            descans_data, registre_data, informe_data = [], [], []
            print_progress(i, NUM_REGISTRES, "Registres Diaris i Descans")
    cur.close()

def main():
    try:
        print(f"Connectant a PostgreSQL (Host: {DB_HOST}, DB: {DB_NAME}, User: {DB_USER})...")
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        print("Connexió establerta correctament.")
    except psycopg2.Error as e:
        print(f"Error connectant a la base de dades: {e}")
        sys.exit(1)

    cur = conn.cursor()
    
    print(f"Establint schema '{SCHEMA}'...")
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    cur.execute(f"SET search_path TO {SCHEMA}, public")
    conn.commit()
    
    try:
        print("Creant taules a partir d'esquema_relacional.sql...")
        with open('esquema_relacional.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cur.execute("""
            DROP TABLE IF EXISTS informe_ia CASCADE;
            DROP TABLE IF EXISTS registre_diari CASCADE;
            DROP TABLE IF EXISTS descans CASCADE;
            DROP TABLE IF EXISTS alimentacio CASCADE;
            DROP TABLE IF EXISTS lesio CASCADE;
            DROP TABLE IF EXISTS forca CASCADE;
            DROP TABLE IF EXISTS resistencia CASCADE;
            DROP TABLE IF EXISTS serie CASCADE;
            DROP TABLE IF EXISTS sessio_exercici CASCADE;
            DROP TABLE IF EXISTS exercici CASCADE;
            DROP TABLE IF EXISTS valoracio CASCADE;
            DROP TABLE IF EXISTS sessio_entrenament CASCADE;
            DROP TABLE IF EXISTS ubicacio CASCADE;
            DROP TABLE IF EXISTS atleta CASCADE;
            """)
            cur.execute(sql_script)
            conn.commit()
            print("Taules creades amb èxit.")
    except Exception as e:
        print(f"Error llegint o executant l'esquema_relacional.sql: {e}")
        sys.exit(1)

    generate_and_insert_atletes(conn)
    
    print("\nObtenint els DNI d'atletes creats per a utilitzar a les altres taules...")
    dnis = fetch_all_dnis(conn)
    if not dnis:
        print("No s'han pogut generar atletes. Sortint.")
        sys.exit(1)
        
    generate_and_insert_ubicacions(conn)
    generate_and_insert_lesions(conn, dnis)
    generate_and_insert_sessions_and_valoracions(conn, dnis)
    generate_and_insert_exercicis_and_series(conn, dnis)
    generate_and_insert_registres(conn, dnis)
    
    cur.close()
    conn.close()
    print("\nProcés finalitzat completament! Les dades han estat inserides.")

if __name__ == "__main__":
    main()
