-- Kenya SMB Accounting MVP - Test Users
-- Run this in Supabase SQL Editor AFTER adding the password_hash column

-- Step 1: First run this to add password_hash column (if not already done)
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
UPDATE alembic_version SET version_num = '002_add_password_hash' WHERE version_num = '001_initial';

-- Step 2: Insert test users

-- User: admin@example.com / AdminPass123
INSERT INTO users (email_encrypted, phone_encrypted, national_id_encrypted, first_name, last_name, role, password_hash, is_active, must_change_password)
VALUES ('Lp0CBP1f/bJozbjqAhdCB6bDOcpFfhYmDoZ0aYIoIo+UtJEdb1tSNfPrOeOX', 'W/+oyogqID6/gGFJNG6ctZg2fv68lACRDWeHnpgvnSx8Vb3v+lKKXzs=', 'JJiAFcU8LDBoipFpsgdMq90unxYXFc6r0lpGGG7nEsWkr8Ik', 'System', 'Admin', 'system_admin', '$2b$12$/6yJvsWkftEAHamV5BSk1OpmLU15si9CqcwnH84sW3.fURvfx88EG', true, false);

-- User: business@example.com / BusinessPass123
INSERT INTO users (email_encrypted, phone_encrypted, national_id_encrypted, first_name, last_name, role, password_hash, is_active, must_change_password)
VALUES ('+SFwHZzgN6BabN4sGXtEeRf4ZuFNYEnf/FJ/HOo1dJjFIgrBEFBPQJ4Fo31snBca', 'UXjc9IaF//4CFDxZgrMCod8Tjme5S+XzsfuNhmvZs8WqXEA6utCvTq8=', 'KM3qoiWhYZrlPj8byVFFML5VLHrHWotUimudtRogEk1MehG7', 'Business', 'Owner', 'business_admin', '$2b$12$c98PpR3kk3FH39S5ec0b2eMvMM60qUfxXislQliZC933XSoc4LHmS', true, false);

-- User: bookkeeper@example.com / BookkeeperPass123
INSERT INTO users (email_encrypted, phone_encrypted, national_id_encrypted, first_name, last_name, role, password_hash, is_active, must_change_password)
VALUES ('qmbN5Te14RDCCfCu82RG6jfIBaI6egsNlUR9txUyK9XbvsW87LxNS7hx9UmWC/GQy/Y=', 'DjWuR74heDVr6bzUa0f/cCgV3XLENXcH21dxVlH/GypqQTK4kU2JwdU=', 'l9SJnZpEvie/C+DPUoXK+lOqe0jc3eXtluXpGOYvVvnjaI5u', 'Book', 'Keeper', 'bookkeeper', '$2b$12$Jwvf1zzOv6HR8ZczSBy6CekRMBqvXYGMKV6Mj7UZQPolDQYppv2HW', true, false);

-- User: onboarding@example.com / OnboardPass123
INSERT INTO users (email_encrypted, phone_encrypted, national_id_encrypted, first_name, last_name, role, password_hash, is_active, must_change_password)
VALUES ('vIOhH5ka5lxOTRl7zAd65doyWXdlo1KJTRWhD/N9aSFcoLxq4C80FCpfQSfzsolYzoo=', '4Icjs9iCiV03+dOlYz6+vCGyb8CTx1Mz72hxa3CzZBGGu+Oq06DbHIA=', 'RBp8JCbpDQzc0zVbyaevS1eAVTrvdA375luXObuMzw4cFhvy', 'Onboarding', 'Agent', 'onboarding_agent', '$2b$12$ZfR07h4DAYjjS9yzm3dO3e/NVAQWHAhCTEK0lqxYVVZ26ifq/gEKW', true, false);

-- User: support@example.com / SupportPass123
INSERT INTO users (email_encrypted, phone_encrypted, national_id_encrypted, first_name, last_name, role, password_hash, is_active, must_change_password)
VALUES ('lWDckgD2tRnUYVd9PmOLGEcSeQiDnwZ8rmjW1+m3T/H2jj66IoeQSwKG3MUxTJo=', 'uEvsRVKbMxljlQXrSMAXbhXgr/l5T6sF+mnVubiNqIhW8BlHEcXIV7A=', 'peOox1Oxq51RqTrY6T+I5TGr9q1ywg7uCp8e/q2X+KKYBvpd', 'Support', 'Agent', 'support_agent', '$2b$12$2D69QLE6zyOUsF6ZM5Ka2.cgGBgF7Eg9pnpr5aTZsbR6DqfvMXGSi', true, false);

-- Test User Credentials:
-- +--------------------------+-------------------+-------------------+
-- | Email                    | Password          | Role              |
-- +--------------------------+-------------------+-------------------+
-- | admin@example.com        | AdminPass123      | system_admin      |
-- | business@example.com     | BusinessPass123   | business_admin    |
-- | bookkeeper@example.com   | BookkeeperPass123 | bookkeeper        |
-- | onboarding@example.com   | OnboardPass123    | onboarding_agent  |
-- | support@example.com      | SupportPass123    | support_agent     |
-- +--------------------------+-------------------+-------------------+
