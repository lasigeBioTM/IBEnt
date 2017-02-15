DROP DATABASE IF EXISTS ibent;
CREATE DATABASE ibent;
USE ibent;

CREATE TABLE corpus (id int NOT NULL AUTO_INCREMENT,
                     corpustag VARCHAR(200),
                     version VARCHAR(20),
                     description VARCHAR(500),
                     PRIMARY KEY (id));

CREATE TABLE document (id int NOT NULL AUTO_INCREMENT,
                       doctag VARCHAR(50) UNIQUE,
                       corpustag VARCHAR(50),
                       title MEDIUMTEXT,
                       doctext TEXT,
                       PRIMARY KEY (id));

CREATE TABLE sentence (id int NOT NULL AUTO_INCREMENT,
                       senttag VARCHAR(50) UNIQUE,
                       doctag VARCHAR(50) UNIQUE,
                       senttext TEXT,
                       sentoffset int,
                       corenlp TEXT,
                       PRIMARY KEY (id));

CREATE TABLE offset (id int NOT NULL AUTO_INCREMENT,
                     doctag VARCHAR(50),
                     senttag VARCHAR(50),
                     docstart int,
                     docend int,
                     sentstart int,
                     sentend int,
                     offsettext TEXT,
                     PRIMARY KEY (id),
                     UNIQUE(doctag, docstart, docend));

CREATE TABLE entity (id int NOT NULL AUTO_INCREMENT,
                     offsetid int,
                     annotationset int,
                     etype VARCHAR(50),
                     createdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     norm_label VARCHAR(50),
                     norm_score float,
                     PRIMARY KEY (id),
                     UNIQUE(offsetid, annotationset));

CREATE TABLE annotationset (id int NOT NULL AUTO_INCREMENT,
                            name VARCHAR(50) UNIQUE,
                            PRIMARY KEY (id));

CREATE TABLE entitypair (id int NOT NULL AUTO_INCREMENT,
                         entity1 int,
                         entity2 int,
                         PRIMARY KEY (id),
                         UNIQUE(entity1, entity2));

create TABLE relation (id int NOT NULL AUTO_INCREMENT,
                       entitypair int,
                       annotationset int,
                       relationtype VARCHAR(50),
                       createdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (id),
                       UNIQUE(entitypair, annotationset));

DROP PROCEDURE IF EXISTS addoffset;
DELIMITER //
CREATE PROCEDURE addoffset(IN docstart int, IN docend int, IN sentstart int, IN sentend int, IN doctag VARCHAR(50), IN senttag VARCHAR(50), IN text TEXT, OUT offsetid int)
  BEGIN
  #DECLARE offsetcount INT DEFAULT 0;
  SELECT offset.id INTO offsetid
  FROM offset
  WHERE offset.docstart = docstart AND offset.docend = docend AND offset.doctag = doctag;
  IF offsetid is NULL THEN
    INSERT INTO offset(doctag, senttag, docstart, docend, sentstart, sentend, offsettext) VALUES (doctag, senttag, docstart, docend, sentstart, sentend, text);
    SELECT offset.id INTO offsetid
    FROM offset
    WHERE offset.docstart = docstart AND offset.docend = docend AND offset.doctag = doctag;
  END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS addpair;
DELIMITER //
CREATE PROCEDURE addpair(IN e1start int, IN e1end int, IN e2start int, IN e2end int, IN doctag VARCHAR(50), IN senttag VARCHAR(50), OUT pairid int)
  BEGIN
  DECLARE entity1id INT;
  DECLARE entity2id INT;
  SELECT p.id INTO pairid
  FROM offset o1, offset o2, entity e1, entity e2, entitypair p
  WHERE o1.docstart = e1start AND o1.docend = e1end AND o2.docstart = e2start AND o2.docend = e2end AND
        e1.offsetid = o1.id AND e2.offsetid = o2.id AND p.entity1 = e1.id AND p.entity2 = e2.id AND
        o1.doctag = doctag AND o2.doctag = doctag;
  IF pairid is NULL THEN
    SELECT e1.id, e2.id INTO entity1id, entity2id
    FROM offset o1, offset o2, entity e1, entity e2
    WHERE o1.docstart = e1start AND o1.docend = e1end AND o2.docstart = e2start AND o2.docend = e2end AND
        e1.offsetid = o1.id AND e2.offsetid = o2.id AND
        o1.doctag = doctag AND o2.doctag = doctag;
    INSERT INTO entitypair(entity1, entity2) VALUES (entity1id, entity2id);
    SELECT p.id INTO pairid
    FROM entitypair p
    WHERE p.entity1 = entity1id AND p.entity2 = entity2id;
  END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS getrelations;
DELIMITER //
CREATE PROCEDURE getrelations(IN doctag VARCHAR(50))
  BEGIN
    SELECT DISTINCT o1.offsettext, o1.docstart, o1.docend, e1.etype, o2.offsettext, o2.docstart, o2.docend, e2.etype, r.relationtype
                   FROM relation r, entitypair p, offset o1, offset o2, entity e1, entity e2, annotationset a
                   WHERE o1.doctag = doctag AND o2.doctag = doctag AND
                         e1.offsetid = o1.id AND e2.offsetid = o2.id AND
                         p.entity1 = e1.id AND p.entity2 = e2.id AND
                         ((e1.id = p.entity1 AND e2.id = p.entity2) OR (e1.id = p.entity2 AND e2.id = p.entity1)) AND
                         r.entitypair = p.id;

  END //
DELIMITER ;