#!/usr/bin/env python3
"""
import_dump.py

Creates the database (if missing) and imports `helpticket_system.sql` into it
using PyMySQL. Run from the project root:

python import_dump.py

Notes:
- Assumes PyMySQL is installed (it's in requirements.txt as PyMySQL).
- Connects to 127.0.0.1:3307 as root with password Jace102020. by default.
- For large or complex dumps it's still recommended to use the native `mysql` client.
"""
import os
import sys
import pymysql

HOST = os.environ.get("DB_HOST", "127.0.0.1")
PORT = int(os.environ.get("DB_PORT", "3307"))
USER = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASS", os.environ.get("DB_PASSWORD", "Jace102020."))
DB_NAME = os.environ.get("DB_NAME", "helpticket_system")
DUMP_FILE = os.environ.get("DUMP_FILE", "helpticket_system.sql")

if not os.path.exists(DUMP_FILE):
    print(f"Error: dump file not found: {DUMP_FILE}")
    sys.exit(1)

print(f"Connecting to {HOST}:{PORT} as {USER}")
try:
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, autocommit=True)
except Exception as e:
    print("ERROR: Could not connect to MySQL:", e)
    sys.exit(1)

cur = conn.cursor()

print(f"Creating database `{DB_NAME}` if it does not exist...")
try:
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
except Exception as e:
    print("ERROR creating database:", e)
    cur.close()
    conn.close()
    sys.exit(1)

print("Database ensured.")

print(f"Selecting database `{DB_NAME}` and importing {DUMP_FILE}...")
conn.select_db(DB_NAME)

# Read file
with open(DUMP_FILE, "r", encoding="utf-8", errors="ignore") as fh:
    sql = fh.read()

# Normalize line endings
sql = sql.replace('\r\n', '\n')

# Remove common comment lines
lines = []
for line in sql.split('\n'):
    stripped = line.strip()
    if stripped.startswith('--') or stripped.startswith('#') or stripped == '':
        continue
    lines.append(line)
cleaned = '\n'.join(lines)

# Split statements by semicolon on its own line where possible
# This is a best-effort splitter; very complex dumps may still require the mysql client.
stmts = []
buffer = []
for line in cleaned.split('\n'):
    buffer.append(line)
    if line.strip().endswith(';'):
        stmt = '\n'.join(buffer).strip()
        stmts.append(stmt[:-1].strip())
        buffer = []
# Add any trailing statement
if buffer:
    trailing = '\n'.join(buffer).strip()
    if trailing:
        stmts.append(trailing)

executed = 0
failed = 0
for stmt in stmts:
    if not stmt:
        continue
    try:
        cur.execute(stmt)
        executed += 1
    except Exception as e:
        failed += 1
        print('\n-- Failed statement --')
        print(e)
        print(stmt[:300])

print(f"Import finished. Executed: {executed}, Failed: {failed}")
cur.close()
conn.close()

if failed:
    print("Some statements failed during import. For a full import, please use the native mysql client or MySQL Workbench if available.")
else:
    print("Import completed successfully.")
