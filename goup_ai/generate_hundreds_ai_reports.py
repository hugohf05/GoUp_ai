import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goup_ai.settings')
django.setup()

from core.models import RegistreDiari, InformeIA

# Phrases for Entrenament
entrenament_phrases = [
    "Basat en el teu HRV d'avui, es recomana reduir la intensitat. ",
    "Molt bona adaptabilitat! Estàs preparat per a una sessió de càrrega màxima. ",
    "El teu registre indica fatiga acumulada i dolor articular. Descansa absolutament avui de qualsevol impacte. ",
    "Les teves dades mostren una progressió lineal excel·lent en la resistència. ",
    "Avui és dia de manteniment. Tria una ubicació exterior si és possible. ",
    "L'algoritme detecta una baixada de rendiment en sèries llargues. ",
    "Estàs en el teu pic de forma del mes! Aprofita-ho per intentar batre el teu PR. "
]
entrenament_details = [
    "Canvia la sessió de sèries de Força per una sessió de recuperació activa de Resistència en zona 2 durant 45 minuts.",
    "Focalitza't en aixecaments compostos (Squat, Deadlift) i intenta superar la teva marca de volum total en un 5%.",
    "L'IA ha reprogramat la teva sessió de Hyrox per d'aquí a dos dies.",
    "Avui toca treball de intervals. 5x1000m a ritme de llindar amb 2 minuts de recuperació.",
    "L'entrenament recomanat és un Trail suau per terreny irregular per enfortir l'estabilitat del turmell.",
    "Recomanem una sessió de mobilitat articular focalitzada en el tren inferior de 30 minuts.",
    "Realitza una sessió de força explosiva amb moviments olímpics (Cleans, Snatches) mantenint les repeticions baixes."
]

# Phrases for Alimentacio
alimentacio_phrases = [
    "Atès que el teu pes ha fluctuat cap a baix, incrementa la ingesta de carbohidrats complexos. ",
    "Els teus nivells d'energia estan òptims. Segueix amb el patró nutricional actual. ",
    "Augmenta la ingesta de greixos saludables (Omega-3) per ajudar a combatre la inflamació sistèmica. ",
    "Per donar suport als intervals d'avui, assegura un àpat ric en carbohidrats simples 60 minuts abans. ",
    "Tens programat el dia trampa o 'refeed'. L'algoritme permet augmentar les calories lliurement fins a un 20%. ",
    "Cal una recàrrega de glicogen moderada. ",
    "Vigila la hidratació avui, els teus marcadors indiquen lleugera deshidratació. "
]
alimentacio_details = [
    "Mantén la proteïna estable a 2.2g/kg de pes corporal en l'últim àpat del dia.",
    "Recorda la importància de la hidratació intra-entrenament afegint electròlits a la teva beguda.",
    "Una ració extra de salmó o llavors de xia ajudarà. Redueix les calories avui unes 300 kcal.",
    "Prescindeix de fibra abans d'entrenar per evitar molèsties gastrointestinals.",
    "Gaudeix d'un àpat abundant però evita greixos saturats si entrenes l'endemà al matí.",
    "Afegeix 5g de creatina monohidrat a la teva rutina post-entrenament.",
    "Intenta fer un dejuni intermitent suau de 12 hores aquesta nit per millorar la sensibilitat a la insulina."
]

# Phrases for Descans
descans_phrases = [
    "Has registrat una baixada significativa en la fase de son profund (Deep Sleep). ",
    "El teu temps de son REM està en els percentils més alts. ",
    "Prioritza el descans avui. L'objectiu és aconseguir mínim 8 hores de son total. ",
    "L'estat de recuperació està en 4/5. Continues responent bé a la càrrega. ",
    "El nivell d'estrès marcat és elevat. Es recomana afegir tècniques de relaxació. ",
    "La teva latència de son és excel·lent, caus adormit de seguida. ",
    "L'algoritme ha detectat massa interrupcions del son (fase Despert). "
]
descans_details = [
    "Evita l'exposició a llum blava 2 hores abans de dormir i considera afegir una suplementació de Magnesi Bisglicinat.",
    "Això indica una excel·lent recuperació cognitiva i del sistema nerviós. Intenta mantenir aquest horari de son.",
    "Procura dormir en una habitació totalment a les fosques i amb una temperatura al voltant dels 18-19 graus.",
    "Fes servir el Foam Roller al tren inferior abans d'anar a dormir per disminuir la tensió miofascial.",
    "Fes 10 minuts de tècniques de respiració o 'Box Breathing' abans d'anar a dormir per activar el sistema nerviós parasimpàtic.",
    "Continua evitant el cafè i els estimulants a partir de les 16:00.",
    "Et recomanem intentar anar al llit 30 minuts abans de l'habitual durant els propers 3 dies."
]

def create_reports():
    print("Buscant registres diaris lliures...")
    # Obtenir 500 registres diaris que NO tenen un InformeIA assignat encara
    registres_sense_informe = list(RegistreDiari.objects.filter(informeIA__isnull=True)[:500])
    
    informes_a_crear = []
    
    for reg in registres_sense_informe:
        e1 = random.choice(entrenament_phrases)
        e2 = random.choice(entrenament_details)
        a1 = random.choice(alimentacio_phrases)
        a2 = random.choice(alimentacio_details)
        d1 = random.choice(descans_phrases)
        d2 = random.choice(descans_details)
        
        informe = InformeIA(
            registre_diari=reg,
            recomanacio_entrenament=e1 + e2,
            recomanacio_alimentacio=a1 + a2,
            recomanacio_descans=d1 + d2
        )
        informes_a_crear.append(informe)
        
    print(f"S'han preparat {len(informes_a_crear)} Informes d'IA. Inserint a la base de dades...")
    InformeIA.objects.bulk_create(informes_a_crear, ignore_conflicts=True)
    print("Miliars de lletres generades i guardades amb èxit!")

if __name__ == "__main__":
    create_reports()
