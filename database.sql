CREATE DATABASE IF NOT EXISTS aicropcare_db;

USE aicropcare_db;

-- 1. Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    role ENUM('farmer','admin') DEFAULT 'farmer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Crops Table
CREATE TABLE crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Disease Information Table
CREATE TABLE diseases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    disease_name VARCHAR(150) NOT NULL,
    crop_name VARCHAR(100),
    symptoms TEXT,
    treatment TEXT,
    prevention TEXT
);

-- 4. Detection History Table
CREATE TABLE detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    crop_name VARCHAR(100),
    image_path VARCHAR(255),
    disease_name VARCHAR(150),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- 5. Weather Information Table
CREATE TABLE weather_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    location VARCHAR(150),
    temperature FLOAT,
    humidity FLOAT,
    rainfall FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- Sample crop information
INSERT INTO crops (crop_name, description) VALUES
('Rice', 'Paddy crop'),
('Tomato', 'Vegetable crop'),
('Cotton', 'Commercial crop'),
('Maize', 'Food and fodder crop'),
('Potato', 'Vegetable crop');

-- Sample disease information
INSERT INTO diseases
(disease_name, crop_name, symptoms, treatment, prevention)
VALUES
('Leaf Blast', 'Rice',
 'Diamond-shaped spots on leaves',
 'Consult an agricultural expert for suitable treatment',
 'Use healthy seeds and monitor crop health'),

('Early Blight', 'Tomato',
 'Brown spots with concentric rings',
 'Remove affected leaves and seek suitable treatment advice',
 'Maintain proper spacing and avoid overhead watering'),

('Bacterial Blight', 'Cotton',
 'Dark lesions and leaf damage',
 'Consult an agricultural expert',
 'Use healthy seeds and follow field sanitation');