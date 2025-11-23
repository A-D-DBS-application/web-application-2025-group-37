-- Voeg role kolom toe aan user tabel voor rolgebaseerde toegangscontrole
-- Rollen: depot_manager, finance_manager, admin

-- Voeg role kolom toe met default 'depot_manager'
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'depot_manager';

-- Update bestaande users (indien nodig, pas aan naar jouw situatie)
-- UPDATE "user" SET role = 'depot_manager' WHERE role IS NULL;

-- Voeg een constraint toe om alleen geldige rollen toe te staan
ALTER TABLE "user" DROP CONSTRAINT IF EXISTS user_role_check;
ALTER TABLE "user" ADD CONSTRAINT user_role_check 
    CHECK (role IN ('depot_manager', 'finance_manager', 'admin'));

-- Maak een index voor snellere rol lookups
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);
