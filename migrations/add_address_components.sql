-- Migration: Add address component columns to member table
-- Date: 2025-11-23

ALTER TABLE member 
ADD COLUMN IF NOT EXISTS street VARCHAR(120),
ADD COLUMN IF NOT EXISTS house_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS postcode VARCHAR(20),
ADD COLUMN IF NOT EXISTS city VARCHAR(120);

-- Optional: Parse existing address data into components
-- This is commented out - uncomment if you want to try splitting existing addresses
-- UPDATE member SET 
--   street = CASE WHEN address IS NOT NULL THEN split_part(address, ',', 1) ELSE NULL END,
--   city = CASE WHEN address IS NOT NULL THEN TRIM(split_part(address, ',', 2)) ELSE NULL END
-- WHERE address IS NOT NULL;
