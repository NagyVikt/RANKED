CREATE DATABASE seoreoco_ranked;

USE seoreoco_ranked;

CREATE TABLE DomainCim (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL,
    plan_id INT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES Plan(id)
);

CREATE TABLE Plan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE Keyword (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL
);

CREATE TABLE ProductName (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE AI_Version (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version_name VARCHAR(50) NOT NULL,
    plan_id INT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES Plan(id)
);

CREATE TABLE EmailStatistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_id INT NOT NULL,
    emails_out INT NOT NULL,
    links_achieved INT NOT NULL,
    links_processing INT NOT NULL,
    links_lost INT NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES DomainCim(id)
);

CREATE TABLE SiteRanking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_id INT NOT NULL,
    gained_ranking INT NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES DomainCim(id)
);

-- Insert initial data for plans
INSERT INTO Plan (name) VALUES ('DEMO'), ('BASIC'), ('STARTER'), ('EXPERT');

-- Insert initial data for domains
INSERT INTO DomainCim (domain_name, plan_id) VALUES 
('EZ PLAN ALAPJAN', 2), 
('BASIC PLAN 1', 3),
('STARTER 2', 4);

-- Insert initial data for keywords
INSERT INTO Keyword (keyword) VALUES 
('Keyword1'), 
('Keyword2'),
('Keyword3');

-- Insert initial data for product names
INSERT INTO ProductName (name) VALUES 
('Product1'), 
('Product2'),
('Product3');

-- Insert initial data for AI versions
INSERT INTO AI_Version (version_name, plan_id) VALUES 
('GPT-4O', 4), 
('GPT-4', 3),
('GPT-3', 1);
