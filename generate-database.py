import pandas as pd
import sqlite3
import os
import csv

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
cur.execute("PRAGMA mmap_size = 10737418240")  # Set the maximum memory map size to 10 GiB

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

# fix incorrectly labled prefered parts from file
component_codes = []
with open(os.path.join("scraped", "ComponentList.csv"), "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row
    for row in reader:
        component_codes.append(row[0])

for code in component_codes:
    cur.execute("SELECT 1 FROM components WHERE lcsc = ?", (code,))
    if cur.fetchone():
        cur.execute(
            "UPDATE components SET preferred = 1 WHERE lcsc = ? AND basic = 0 AND preferred = 0",
            (code,),
        )
        conn.commit()

optimized_db_size = os.path.getsize("jlcpcb-components.sqlite3")
print(f"Optimized Database Size: {optimized_db_size / (1024 ** 3):.2f} GiB")

# Retrieve basic/preferred components ($0 for loading feeders)
cur.execute(
    """
    SELECT * FROM v_components 
    WHERE (basic > 0 OR preferred > 0);
"""
)
filtered_components = cur.fetchall()

# Create Pandas DataFrame and sort components
df = pd.DataFrame(filtered_components, columns=[desc[0] for desc in cur.description])
df_sorted = df.sort_values(by=["category", "subcategory", "package"])

# Save sorted DataFrame to CSV
df_sorted.to_csv("jlcpcb-components-basic-preferred.csv", index=False, header=True)

cur.execute("PRAGMA analyze")  # Update statistics for the query planner to improve query performance
cur.execute("PRAGMA optimize")  # Perform various optimizations, such as reindexing and refreshing views
conn.close()
