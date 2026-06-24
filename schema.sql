-- ============================================================
-- Maroc Authentique — MySQL schema + seed data
-- Usage:  mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS maroc_authentique
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE maroc_authentique;

-- ---------- Villages ----------
DROP TABLE IF EXISTS villages;
CREATE TABLE villages (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(160) NOT NULL,
  region      VARCHAR(120) NOT NULL,
  type        ENUM('Montagne', 'Désert', 'Culturel', 'Naturel') NOT NULL,
  description TEXT NOT NULL,
  price       DECIMAL(10,2) NOT NULL DEFAULT 0,
  image       VARCHAR(255) NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- Users (authentication) ----------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(160) NOT NULL,
  email         VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- Reservations ----------
DROP TABLE IF EXISTS reservations;
CREATE TABLE reservations (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(160) NOT NULL,
  email        VARCHAR(160) NOT NULL,
  visit_date   DATE NOT NULL,
  place        VARCHAR(160) NOT NULL,
  visitor_type ENUM('National', 'Étranger') NOT NULL DEFAULT 'National',
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- Seed villages ----------
INSERT INTO villages (name, region, type, description, price, image) VALUES
('Vallée d''Aït Bouguemez', 'Haut Atlas', 'Montagne',
 'La « vallée heureuse » : terrasses verdoyantes, villages de pisé et hospitalité berbère.',
 450.00, 'static/images/village-aitbouguemez.png'),

('Dunes de Tinfou', 'Drâa-Tafilalet', 'Désert',
 'Des dunes dorées loin de la foule de Merzouga, idéales pour une nuit sous les étoiles.',
 600.00, 'static/images/village-desert.png'),

('Cascades d''Akchour', 'Rif', 'Naturel',
 'Bassins turquoise et pont naturel de Dieu au cœur du parc de Talassemtane.',
 300.00, 'static/images/village-cascade.png'),

('Lac d''Imilchil', 'Haut Atlas', 'Culturel',
 'Lacs d''altitude et célèbre moussem des fiançailles des Aït Haddidou.',
 520.00, 'static/images/village-imilchil.png'),

('Kasbah de Tamnougalt', 'Vallée du Drâa', 'Culturel',
 'Ancienne kasbah de terre ocre entourée d''une palmeraie luxuriante.',
 380.00, 'static/images/village-kasbah.png'),

('Village bleu de Chefchaouen', 'Rif', 'Naturel',
 'Ruelles bleues hors des circuits touristiques, ateliers d''artisans et calme montagnard.',
 340.00, 'static/images/village-bluevillage.png');
