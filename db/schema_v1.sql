-- Enable GIS extensions for location logic
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    cadastre_id VARCHAR(50) UNIQUE NOT NULL, -- The official identifier
    address_street VARCHAR(255),
    address_number VARCHAR(50),
    neighborhood VARCHAR(100),
    gps_coordinates GEOMETRY(Point, 4326),
    construction_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    source_url TEXT UNIQUE NOT NULL,
    price_bgn DECIMAL(12, 2),
    advertised_area_sqm DECIMAL(10, 2),
    description_raw TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    listing_id INT REFERENCES listings(id),
    building_id INT REFERENCES buildings(id),
    risk_score INT, -- 0 to 100 (100 is Toxic)
    is_address_verified BOOLEAN DEFAULT FALSE,
    discrepancy_details JSONB, -- Stores the "Apartment vs Atelier" logic
    cost_to_generate DECIMAL(10, 4) -- Tracking the $0.22 API cost
);
