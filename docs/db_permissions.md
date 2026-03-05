# Database Permission Setup

## Grant all permissions to ruo user

```sql
-- Grant all privileges on existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ruo;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ruo;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ruo;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ruo;
```

## Docker execution

```bash
docker exec -i ruo_postgres psql -U ruo_user -d ruo -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ruo;"
docker exec -i ruo_postgres psql -U ruo_user -d ruo -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ruo;"
docker exec -i ruo_postgres psql -U ruo_user -d ruo -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ruo; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ruo;"
```
