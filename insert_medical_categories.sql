-- SQL script to insert medical categories
-- Run this in SQLite browser or command line

INSERT OR IGNORE INTO veteran_app_medicalcategory (name, description) VALUES
('S1A1', 'Fit for all duties'),
('S1A2', 'Fit for all duties with minor restrictions'),
('S2A2', 'Fit for limited duties'),
('S2A3', 'Fit for limited duties with restrictions'),
('S3A3', 'Temporarily unfit'),
('S4A4', 'Permanently unfit for service');

-- Verify the data
SELECT * FROM veteran_app_medicalcategory;