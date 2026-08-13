-- One-time PostgreSQL authorization bootstrap for a new personal GCP project.
--
-- Run as the built-in PostgreSQL administrator in Cloud SQL Studio after
-- replacing the three YOUR_* role placeholders with the Terraform IAM database
-- usernames. Do not commit a copy containing real project identifiers.
--
-- This script is idempotent. Run it once before the first migration; the ALTER
-- DEFAULT PRIVILEGES statements grant runtime access to tables subsequently
-- created by the migration identity.

BEGIN;

GRANT CONNECT ON DATABASE financialos TO "YOUR_MIGRATE_DATABASE_USER";
GRANT CONNECT ON DATABASE financialos TO "YOUR_API_DATABASE_USER";
GRANT CONNECT ON DATABASE financialos TO "YOUR_WORKER_DATABASE_USER";

GRANT USAGE, CREATE ON SCHEMA public TO "YOUR_MIGRATE_DATABASE_USER";
GRANT USAGE ON SCHEMA public TO "YOUR_API_DATABASE_USER";
GRANT USAGE ON SCHEMA public TO "YOUR_WORKER_DATABASE_USER";

ALTER DEFAULT PRIVILEGES FOR ROLE "YOUR_MIGRATE_DATABASE_USER" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "YOUR_API_DATABASE_USER";
ALTER DEFAULT PRIVILEGES FOR ROLE "YOUR_MIGRATE_DATABASE_USER" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "YOUR_WORKER_DATABASE_USER";

-- These grants are harmless before the first migration and make the script safe
-- to rerun after a migration if tables already exist.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
  TO "YOUR_API_DATABASE_USER";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
  TO "YOUR_WORKER_DATABASE_USER";

COMMIT;
