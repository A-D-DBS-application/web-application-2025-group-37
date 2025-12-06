-- Add code column to bike table
ALTER TABLE bike ADD COLUMN IF NOT EXISTS code VARCHAR(50);
