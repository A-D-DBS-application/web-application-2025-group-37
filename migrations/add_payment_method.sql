-- Add method column to payment table
ALTER TABLE payment ADD COLUMN IF NOT EXISTS method VARCHAR(20) DEFAULT 'cash';

-- Update existing records to have cash as default method
UPDATE payment SET method = 'cash' WHERE method IS NULL;
