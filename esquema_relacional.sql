-- ------------------------------------------------------------
-- CREACIÓ DE L'SCHEMA 'practica'
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS practica;
SET search_path TO practica, public;

-- ------------------------------------------------------------
-- TAULA: atleta
-- Entitat principal del sistema.
-- correu i numero_telefon les hem escollit com a claus alternatives (UNIQUE).
-- ------------------------------------------------------------
CREATE TABLE atleta (
    dni_atleta          VARCHAR(20)     NOT NULL,
    nom                 VARCHAR(100)    NOT NULL,
    data_naixement      DATE            NOT NULL,
    correu              VARCHAR(150)    NOT NULL,
    numero_telefon      VARCHAR(20)     NOT NULL,
    pes                 DECIMAL(5,2)    NOT NULL CHECK (pes > 0),
    composicio_corporal VARCHAR(200)    NOT NULL CHECK (composicio_corporal > 0),
    altura              DECIMAL(5,2)    NOT NULL CHECK (altura > 0),
    objectiu            VARCHAR(100)    NOT NULL,
    activitat_fisica_diaria VARCHAR(15) NOT NULL
        CHECK (activitat_fisica_diaria IN ('SEDENTARI', 'ACTIU', 'MOLT_ACTIU')),
    estat               VARCHAR(10)     NOT NULL
        CHECK (estat IN ('ACTIU', 'LESIONAT')),

    CONSTRAINT pk_atleta         PRIMARY KEY (dni_atleta),
    CONSTRAINT uk_atleta_correu  UNIQUE (correu),
    CONSTRAINT uk_atleta_telefon UNIQUE (numero_telefon)
);


-- ------------------------------------------------------------
-- TAULA: ubicacio
-- Lloc físic on es duu a terme una sessió d'entrenament.
-- ------------------------------------------------------------
CREATE TABLE ubicacio (
    id_ubicacio     INT             NOT NULL,
    tipus_ubicacio  VARCHAR(10)     NOT NULL
        CHECK (tipus_ubicacio IN ('EXTERIOR', 'INTERIOR')),
    adreca          VARCHAR(200)    NOT NULL,

    CONSTRAINT pk_ubicacio PRIMARY KEY (id_ubicacio)
);

-- ------------------------------------------------------------
-- TAULA: valoracio
-- Classe associativa entre atleta i ubicacio.
-- Un atleta només pot valorar una ubicació si hi ha fet
-- una sessió d'entrenament.
-- ------------------------------------------------------------
CREATE TABLE valoracio (
    dni_atleta      VARCHAR(20)     NOT NULL,
    id_ubicacio     INT             NOT NULL,
    valoracio       DECIMAL(2,1)    NOT NULL CHECK (valoracio BETWEEN 0 AND 5),
    comentaris      TEXT            NULL,

    CONSTRAINT pk_valoracio         PRIMARY KEY (dni_atleta, id_ubicacio),
    CONSTRAINT fk_valoracio_atleta  FOREIGN KEY (dni_atleta)  REFERENCES atleta (dni_atleta),
    CONSTRAINT fk_valoracio_ubic    FOREIGN KEY (id_ubicacio) REFERENCES ubicacio (id_ubicacio)
);


-- ------------------------------------------------------------
-- TAULA: sessio_entrenament
-- Cada sessió pertany a un atleta i es realitza en una ubicació.
-- ------------------------------------------------------------
CREATE TABLE sessio_entrenament (
    id_sessio       INT             NOT NULL,
    dni_atleta      VARCHAR(20)     NOT NULL,
    id_ubicacio     INT             NOT NULL,
    data            DATE            NOT NULL,
    duracio_total   INTERVAL        NOT NULL CHECK (duracio_total > INTERVAL '0'),
    comentaris      TEXT,

    CONSTRAINT pk_sessio            PRIMARY KEY (id_sessio),
    CONSTRAINT fk_sessio_atleta     FOREIGN KEY (dni_atleta)  REFERENCES atleta (dni_atleta),
    CONSTRAINT fk_sessio_ubicacio   FOREIGN KEY (id_ubicacio) REFERENCES ubicacio (id_ubicacio)
);


-- ------------------------------------------------------------
-- TAULA: exercici
-- Creat per un atleta concret. Pot aparèixer en diverses sessions.
-- ------------------------------------------------------------
CREATE TABLE exercici (
    id_ex               INT             NOT NULL,
    dni_atleta          VARCHAR(20)     NOT NULL,
    nom                 VARCHAR(100)    NOT NULL,
    descripcio          TEXT            NULL,
    descans_entre_series INTERVAL       NULL,

    CONSTRAINT pk_exercici          PRIMARY KEY (id_ex),
    CONSTRAINT fk_exercici_atleta   FOREIGN KEY (dni_atleta) REFERENCES atleta (dni_atleta)
);


-- ------------------------------------------------------------
-- TAULA: sessio_exercici
-- Taula d'associació N:M entre sessio_entrenament i exercici.
-- ------------------------------------------------------------
CREATE TABLE sessio_exercici (
    id_sessio   INT NOT NULL,
    id_ex       INT NOT NULL,

    CONSTRAINT pk_sessio_exercici       PRIMARY KEY (id_sessio, id_ex),
    CONSTRAINT fk_se_sessio             FOREIGN KEY (id_sessio) REFERENCES sessio_entrenament (id_sessio),
    CONSTRAINT fk_se_exercici           FOREIGN KEY (id_ex)     REFERENCES exercici (id_ex)
);


-- ------------------------------------------------------------
-- TAULA: serie
-- Entitat feble d'exercici. Identificada per (id_ex, num_serie).
-- ------------------------------------------------------------
CREATE TABLE serie (
    id_ex       INT     NOT NULL,
    num_serie   INT     NOT NULL,

    CONSTRAINT pk_serie         PRIMARY KEY (id_ex, num_serie),
    CONSTRAINT fk_serie_exercici FOREIGN KEY (id_ex) REFERENCES exercici (id_ex)
);


-- ------------------------------------------------------------
-- TAULA: resistencia
-- Registra les dades de les sèries de resistència.
-- ------------------------------------------------------------
CREATE TABLE resistencia (
    id_ex               INT             NOT NULL,
    num_serie           INT             NOT NULL,
    duracio             INTERVAL        NOT NULL CHECK (duracio > INTERVAL '0'),
    tipus_superficie    VARCHAR(10)     NOT NULL
        CHECK (tipus_superficie IN ('ASFALT', 'CINTA', 'TRAIL')),
    distancia           DECIMAL(4,2)    NOT NULL CHECK (distancia > 0),
    desnivell           DECIMAL(6,2),
    freq_cardiaca_mitjana DECIMAL(4,1)  NOT NULL CHECK (freq_cardiaca_mitjana BETWEEN 30 AND 220),

    CONSTRAINT pk_resistencia       PRIMARY KEY (id_ex, num_serie),
    CONSTRAINT fk_resistencia_serie FOREIGN KEY (id_ex, num_serie) REFERENCES serie (id_ex, num_serie)
);


-- ------------------------------------------------------------
-- TAULA: forca
-- Registra les dades de les sèries de força.
-- ------------------------------------------------------------
CREATE TABLE forca (
    id_ex           INT             NOT NULL,
    num_serie       INT             NOT NULL,
    grup_muscular   VARCHAR(100)    NOT NULL,
    pes             DECIMAL(5,2)    NOT NULL CHECK (pes > 0),
    rpe             INT             NOT NULL CHECK (rpe BETWEEN 0 AND 10),

    CONSTRAINT pk_forca         PRIMARY KEY (id_ex, num_serie),
    CONSTRAINT fk_forca_serie   FOREIGN KEY (id_ex, num_serie) REFERENCES serie (id_ex, num_serie)
);


-- ------------------------------------------------------------
-- TAULA: lesio
-- Registre de les lesions d'un atleta.
-- id_lesio és global (no és entitat feble).
-- RI: data_fi >= data_inici
-- ------------------------------------------------------------
CREATE TABLE lesio (
    id_lesio                INT             NOT NULL,
    dni_atleta              VARCHAR(20)     NOT NULL,
    data_inici              DATE            NOT NULL,
    data_fi                 DATE            NULL,
    zona_afectada           VARCHAR(100)    NOT NULL,
    grau_serietat           INT             NOT NULL CHECK (grau_serietat BETWEEN 0 AND 5),
    estat_actual            VARCHAR(15)     NOT NULL
        CHECK (estat_actual IN ('ACTIVA', 'REHABILITACIO', 'RESOLTA')),
    comentaris_diagnostic   TEXT            NULL,

    CONSTRAINT pk_lesio         PRIMARY KEY (id_lesio, dni_atleta),
    CONSTRAINT fk_lesio_atleta  FOREIGN KEY (dni_atleta) REFERENCES atleta (dni_atleta),
    CONSTRAINT ck_lesio_dates   CHECK (data_fi IS NULL OR data_fi >= data_inici)
);


-- ------------------------------------------------------------
-- TAULA: alimentacio
-- Relació 1:1 amb atleta. Pauta nutricional de l'atleta.
-- ------------------------------------------------------------
CREATE TABLE alimentacio (
    dni_atleta          VARCHAR(20)     NOT NULL,
    tipus_alimentacio   VARCHAR(15)     NOT NULL
        CHECK (tipus_alimentacio IN ('VEGETARIA', 'VEGA', 'OMNIVOR')),
    calories            DECIMAL(7,2)    NOT NULL CHECK (calories > 0),
    proteina            DECIMAL(7,2)    NOT NULL CHECK (proteina > 0),
    carbohidrats        DECIMAL(7,2)    NOT NULL CHECK (carbohidrats > 0),
    grases              DECIMAL(7,2)    NOT NULL CHECK (grases > 0),
    suplementacio       TEXT            NULL,

    CONSTRAINT pk_alimentacio       PRIMARY KEY (dni_atleta),
    CONSTRAINT fk_aliment_atleta    FOREIGN KEY (dni_atleta) REFERENCES atleta (dni_atleta)
);


-- ------------------------------------------------------------
-- TAULA: descans
-- RI: duracio_total = despert + rem + core + deep
-- ------------------------------------------------------------
CREATE TABLE descans (
    dni_atleta      VARCHAR(20)     NOT NULL,
    data_inici      TIMESTAMP       NOT NULL,
    duracio         INT             NOT NULL CHECK (duracio > 0),  -- en minuts
    despert         INT             NOT NULL CHECK (despert >= 0),
    rem             INT             NOT NULL CHECK (rem >= 0),
    core            INT             NOT NULL CHECK (core >= 0),
    deep            INT             NOT NULL CHECK (deep >= 0),
    hrv             DECIMAL(6,2)    NOT NULL CHECK (hrv > 0),

    CONSTRAINT pk_descans           PRIMARY KEY (dni_atleta, data_inici),
    CONSTRAINT fk_descans_atleta    FOREIGN KEY (dni_atleta) REFERENCES atleta (dni_atleta),
    CONSTRAINT ck_descans_duracio   CHECK (duracio = despert + rem + core + deep)
);


-- ------------------------------------------------------------
-- TAULA: registre_diari
-- ------------------------------------------------------------
CREATE TABLE registre_diari (
    dni_atleta                  VARCHAR(20)     NOT NULL,
    data                        DATE            NOT NULL,
    adaptabilitat_alimentacio   DECIMAL(5,2)    NOT NULL CHECK (adaptabilitat_alimentacio BETWEEN 0 AND 100),
    comentaris_entrenaments     TEXT            NULL,
    estat_recuperacio_descans   DECIMAL(2,1)    NOT NULL CHECK (estat_recuperacio_descans BETWEEN 0 AND 5),
    nivell_energia              DECIMAL(2,1)    NOT NULL CHECK (nivell_energia BETWEEN 0 AND 5),
    nivell_estres               DECIMAL(2,1)    NOT NULL CHECK (nivell_estres BETWEEN 0 AND 5),
    sensacions_generals         TEXT            NULL,

    CONSTRAINT pk_registre_diari        PRIMARY KEY (dni_atleta, data),
    CONSTRAINT fk_registre_atleta       FOREIGN KEY (dni_atleta) REFERENCES atleta (dni_atleta)
);


-- ------------------------------------------------------------
-- TAULA: informe_ia
-- Relació 1:1 amb registre_diari.
-- Es genera a partir del registre diari de l'atleta.
-- ------------------------------------------------------------
CREATE TABLE informe_ia (
    dni_atleta                  VARCHAR(20)     NOT NULL,
    data                        DATE            NOT NULL,
    recomanacio_entrenament     TEXT            NOT NULL,
    recomanacio_alimentacio     TEXT            NOT NULL,
    recomanacio_descans         TEXT            NOT NULL,

    CONSTRAINT pk_informe_ia            PRIMARY KEY (dni_atleta, data),
    CONSTRAINT fk_informe_registre      FOREIGN KEY (dni_atleta, data)
                                            REFERENCES registre_diari (dni_atleta, data)
);


-- ============================================================
-- RESTRICCIONS D'INTEGRITAT NO APLICABLES AMB CHECK
-- (s'han d'implementar via software)
-- ============================================================
--
-- RI-1: Un atleta només pot valorar una ubicació si ha realitzat
--       almenys una sessio_entrenament en aquella ubicació.
--
-- RI-2: Si una lesió té estat_actual = 'ACTIVA', l'atribut estat
--       de l'atleta ha de ser 'LESIONAT'.
--
-- RI-3: L'especialització de serie és completa i disjunta:
--       cada tupla de serie ha d'existir exactament a una de les
--       taules resistencia o forca (no a cap, ni a les dues).
--
-- ============================================================

