-- Create the database schema
CREATE DATABASE NSPC_DATA_APP;

-- Use the newly created schema
USE NSPC_DATA_APP;

-- 1. Organization Table
CREATE TABLE Organization (
    org_id BIGINT PRIMARY KEY,
    org_name VARCHAR(45),
    delete_indicator VARCHAR(5)
);

-- 2. State Table
CREATE TABLE State (
    state_id BIGINT(20) PRIMARY KEY,
    state_name VARCHAR(45),
    state_code VARCHAR(45),
    delete_indicator VARCHAR(5)
);

-- 3. Parliment Table
CREATE TABLE Parliment (
    parliment_id BIGINT(20) PRIMARY KEY,
    parliment_name VARCHAR(45),
    parliment_code VARCHAR(45),
    delete_indicator VARCHAR(5),
    state_id BIGINT(20),
    FOREIGN KEY (state_id) REFERENCES State(state_id)
);

-- 4. Assembly Table
CREATE TABLE Assembly (
    assembly_id BIGINT(20) PRIMARY KEY,
    assembly_name VARCHAR(45),
    assembly_code VARCHAR(45),
    delete_indicator VARCHAR(5),
    parliment_id BIGINT(20),
    FOREIGN KEY (parliment_id) REFERENCES Parliment(parliment_id)
);

-- 5. Polling_booth Table
CREATE TABLE Polling_booth (
    booth_id BIGINT(20) PRIMARY KEY,
    booth_name VARCHAR(45),
    delete_indicator VARCHAR(5),
    assembly_id BIGINT(20),
    FOREIGN KEY (assembly_id) REFERENCES Assembly(assembly_id)
);

-- 6. Polling_booth_mapping Table
CREATE TABLE Polling_booth_mapping (
    booth_mapping_id BIGINT(20) PRIMARY KEY,
    booth_name VARCHAR(45), -- Assuming this remains as a separate column (not FK)
    booth_id BIGINT(20),
    org_id BIGINT(20),
    delete_indicator VARCHAR(5),
    FOREIGN KEY (booth_id) REFERENCES Polling_booth(booth_id),
    FOREIGN KEY (org_id) REFERENCES Organization(org_id)
);

-- 7. Master_data Table
CREATE TABLE Master_data (
    master_id BIGINT(20) PRIMARY KEY,
    s_no VARCHAR(5),
    v_id VARCHAR(45) UNIQUE,
    v_name VARCHAR(100),
    relation_name VARCHAR(100),
    relation_type VARCHAR(50),
    address VARCHAR(150),
    age INT,
    gender VARCHAR(1),
    v_status VARCHAR(45),
    contact BIGINT(12)
);



