-- One-time database/role bootstrap. Run as a PostgreSQL superuser, e.g.:
--   psql -U postgres -h localhost -f sql/init_db.sql
--
-- IMPORTANT: edit the password below first, then use the SAME password in .env.
-- Never commit a real password.

\set scrubber_password 'CHANGE_ME_STRONG_PASSWORD'

CREATE ROLE scrubber WITH LOGIN PASSWORD :'scrubber_password';

CREATE DATABASE financial_scrubber
    OWNER scrubber
    ENCODING 'UTF8'
    TEMPLATE template0;
