from core.models import InformeIA, RegistreDiari
import random

def create_realistic_reports():
    # Agafem els primers 5 Informes que existeixin a la base de dades
    informes = InformeIA.objects.all()[:5]
    
    informes_reals = [
        {
            "entrenament": "Basat en el teu HRV d'avui (descens del 15% respecte la mitjana setmanal), es recomana reduir la intensitat. Canvia la sessió de sèries de Força (RPE 9) per una sessió de recuperació activa de Resistència en zona 2 (Freqüència Cardíaca ~130 bpm) durant 45 minuts.",
            "alimentacio": "Atès que el teu pes ha fluctuat cap a baix i l'entrenament de demà és d'alta demanda glucolítica, incrementa la ingesta de carbohidrats complexos en 1.5g/kg de pes corporal en l'últim àpat del dia. Mantén la proteïna estable a 2.2g/kg.",
            "descans": "Has registrat una baixada significativa en la fase de son profund (Deep Sleep). Evita l'exposició a llum blava 2 hores abans de dormir i considera afegir una suplementació de Magnesi Bisglicinat."
        },
        {
            "entrenament": "Molt bona adaptabilitat! Estàs preparat per a una sessió de càrrega màxima. Focalitza't en aixecaments compostos (Squat, Deadlift) i intenta superar la teva marca de volum total en un 5%. Mantingues els descansos entre sèries a 3 minuts.",
            "alimentacio": "Els teus nivells d'energia estan òptims. Segueix amb el patró nutricional actual. Recorda la importància de la hidratació intra-entrenament afegint electròlits a la teva beguda si la sessió supera els 90 minuts.",
            "descans": "El teu temps de son REM està en els percentils més alts. Això indica una excel·lent recuperació cognitiva i del sistema nerviós. Intenta mantenir aquest horari de son d'entre 22:30 i 06:30."
        },
        {
            "entrenament": "El teu registre indica fatiga acumulada i dolor articular. Descansa absolutament avui de qualsevol impacte. Opcionalment, fes 20 minuts de mobilitat i estiraments suaus. L'IA ha reprogramat la teva sessió de Hyrox per d'aquí a dos dies.",
            "alimentacio": "Augmenta la ingesta de greixos saludables (Omega-3) per ajudar a combatre la inflamació sistèmica. Una ració extra de salmó o llavors de xia ajudarà. Redueix les calories avui unes 300 kcal per l'absència d'entrenament.",
            "descans": "Prioritza el descans avui. L'objectiu és aconseguir mínim 8 hores de son total, amb un mínim d'1.5h de son profund."
        },
        {
            "entrenament": "Les teves dades mostren una progressió lineal excel·lent en la resistència. Avui toca treball de intervals. 5x1000m a ritme de llindar amb 2 minuts de recuperació. Fixa't molt en la tècnica de carrera un cop passis la 3a sèrie, ja que la fatiga pot alterar la petjada.",
            "alimentacio": "Per donar suport als intervals d'avui, assegura un àpat ric en carbohidrats simples 60 minuts abans de l'entrenament (per exemple, un plàtan madur i una mica de mel). Prescindeix de fibra per evitar molèsties gastrointestinals.",
            "descans": "L'estat de recuperació està en 4/5. Continues responent bé a la càrrega. Fes servir el Foam Roller al tren inferior abans d'anar a dormir per disminuir la tensió miofascial."
        },
        {
            "entrenament": "Avui és dia de manteniment. Tria una ubicació exterior si és possible, per aprofitar la llum solar i regular els ritmes circadians. L'entrenament recomanat és un Trail suau per terreny irregular per enfortir l'estabilitat del turmell, màxim 60 minuts.",
            "alimentacio": "Tens programat el dia trampa o 'refeed'. L'algoritme permet augmentar les calories lliurement fins a un 20% sobre el teu manteniment. Gaudeix i recarrega reserves de glicogen.",
            "descans": "El nivell d'estrès marcat és elevat (4.5/5). Es recomana afegir 10 minuts de tècniques de respiració o 'Box Breathing' abans d'anar a dormir per activar el sistema nerviós parasimpàtic."
        }
    ]

    for i, informe in enumerate(informes):
        if i < len(informes_reals):
            informe.recomanacio_entrenament = informes_reals[i]["entrenament"]
            informe.recomanacio_alimentacio = informes_reals[i]["alimentacio"]
            informe.recomanacio_descans = informes_reals[i]["descans"]
            informe.save()
            print(f"Informe d'exemple {i+1} actualitzat amb èxit!")

if __name__ == "__main__":
    create_realistic_reports()
