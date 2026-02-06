from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

# ---------- CONFIGURATION ----------
LOCAL_DB = "postgresql://postgres@localhost:5432/helpticket_system_pg"  # No password locally
RENDER_DB = "postgresql://helpticket_system_user:NyXRNEZGBCXl7MFzYFCq7xFx7oEUp0s7@dpg-NEWID.render.com:5432/helpticket_system_pg"
# -----------------------------------

# Connect to local and Render DBs
local_engine = create_engine(LOCAL_DB)
render_engine = create_engine(RENDER_DB)

# Reflect local schema
local_meta = MetaData()
local_meta.reflect(bind=local_engine)

# Create sessions
LocalSession = sessionmaker(bind=local_engine)
RenderSession = sessionmaker(bind=render_engine)

local_session = LocalSession()
render_session = RenderSession()

print("----- DRY-RUN MIGRATION START -----\n")

# Copy data table by table (Dry-Run Mode)
for table in local_meta.sorted_tables:
    print(f"Table: {table.name}")
    
    # Fetch all local rows
    local_rows = local_session.execute(table.select()).fetchall()
    
    # Fetch all primary keys from Render
    render_rows = render_session.execute(table.select()).fetchall()
    render_pks = {tuple(r._mapping[k.name] for k in table.primary_key) for r in render_rows}
    
    # Find rows that do NOT exist in Render
    new_rows = []
    for r in local_rows:
        pk_tuple = tuple(r._mapping[k.name] for k in table.primary_key)
        if pk_tuple not in render_pks:
            new_rows.append(dict(r._mapping))
    
    print(f"   Total local rows: {len(local_rows)}")
    print(f"   Existing rows on Render: {len(render_rows)}")
    print(f"   Rows that WOULD be inserted: {len(new_rows)}\n")

print("----- DRY-RUN MIGRATION END -----\n")

# Close sessions
local_session.close()
render_session.close()
