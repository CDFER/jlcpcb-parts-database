import pandas as pd
import sqlite3
import os
from datetime import datetime, timezone

os.chdir("db_build")

# Rename the database file
os.rename("cache.sqlite3", f"jlcpcb-components.sqlite3")

initial_db_size = os.path.getsize("jlcpcb-components.sqlite3")
print(f"Initial SQLite Database Size: {initial_db_size / (1024 ** 3):.2f} GiB")

conn = sqlite3.connect("jlcpcb-components.sqlite3")
cur = conn.cursor()

cur.execute("PRAGMA journal_mode = WAL")  # Enable Write-Ahead Logging (WAL) for improved performance and concurrency
cur.execute("PRAGMA synchronous = NORMAL")  # Set the synchronous mode to NORMAL, which balances safety and performance
cur.execute("PRAGMA temp_store = MEMORY")  # Store temporary tables and indices in memory for faster access
cur.execute("PRAGMA mmap_size = 536870912")  # Set the maximum memory map size to 512MiB

# Delete components with low stock
cur.execute("DELETE FROM components WHERE stock < 5;")
conn.commit()
print(f"Deleted {cur.rowcount} components with low stock")

# Create an FTS (Full-Text Search) index on multiple columns (helps to speed up searching the database)
cur.execute(
    """
    CREATE VIRTUAL TABLE components_fts USING fts5(
        lcsc,
        mfr,
        package,
        description,
        datasheet,
        content='components'
    );
"""
)
conn.commit()

# Reindex database to reduce file size
cur.execute("REINDEX;")
conn.commit()

# Vacuum database to reduce file size
cur.execute("VACUUM;")
conn.commit()

# Load Scraped Components List
file_location = os.path.join("..", os.path.join("scraped", "ComponentList.csv"))
df = pd.read_csv(file_location)

# Convert date columns to datetime with UTC timezone
df["First Seen"] = pd.to_datetime(df["First Seen"], format="%Y/%m/%d", utc=True)
df["Last Seen"] = pd.to_datetime(df["Last Seen"], format="%Y/%m/%d", utc=True)

# Calculate time differences
now = datetime.now(timezone.utc)
df["Days Since First Seen"] = (now - df["First Seen"]).dt.days
df["Days Since Last Seen"] = (now - df["Last Seen"]).dt.days

# Filter components
component_codes = df[(df["Days Since First Seen"] >= 1) & (df["Days Since Last Seen"] < 2)]["lcsc"].astype(int).tolist()

preferred_parts_corrected = 0
for code in component_codes:
    cur.execute("SELECT 1 FROM components WHERE lcsc = ?", (code,))
    if cur.fetchone():
        cur.execute(
            "UPDATE components SET preferred = 1 WHERE lcsc = ? AND basic = 0 AND preferred = 0",
            (code,),
        )
        conn.commit()
        preferred_parts_corrected += 1

print(f"Preferred Parts Corrected: {preferred_parts_corrected}")

optimized_db_size = os.path.getsize("jlcpcb-components.sqlite3")
print(f"Optimized Database Size: {optimized_db_size / (1024 ** 3):.2f} GiB")

# Retrieve basic/preferred components ($0 for loading feeders) and exclude "0201" package
cur.execute(
    """
    SELECT * FROM v_components 
    WHERE (basic > 0 OR preferred > 0) AND package != '0201';
"""
)
filtered_components = cur.fetchall()

# Create Pandas DataFrame and sort components
df = pd.DataFrame(filtered_components, columns=[desc[0] for desc in cur.description])
df_sorted = df.sort_values(by=["category", "subcategory", "package"])

# Merge assembly details
file_location = os.path.join("..", os.path.join("scraped", "assembly-details.csv"))
df = pd.read_csv(file_location)

df_filtered = df[df["lcsc"].isin(df_sorted["lcsc"])]

df_sorted = pd.merge(
    df_sorted, df_filtered[["lcsc", "Assembly Process", "Min Order Qty", "Attrition Qty"]], on="lcsc", how="right"
)

# Save sorted DataFrame to CSV
df_sorted.to_csv("jlcpcb-components-basic-preferred.csv", index=False, header=True)

cur.execute("PRAGMA analyze")  # Update statistics for the query planner to improve query performance
cur.execute("PRAGMA optimize")  # Perform various optimizations, such as reindexing and refreshing views
conn.close()
