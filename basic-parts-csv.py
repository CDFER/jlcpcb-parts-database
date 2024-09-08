import pandas as pd
import sqlite3
import os

os.chdir("db_build")

initial_db_size = os.path.getsize("cache.sqlite3")
print(f"Initial SQLite Database Size: {initial_db_size / (1024 ** 3):.2f} GiB")

conn = sqlite3.connect("cache.sqlite3")
cur = conn.cursor()

# Delete components with low stock
cur.execute("DELETE FROM components WHERE stock < 5;")
conn.commit()
print(f"Deleted {cur.rowcount} components with low stock")

# Vacuum database to reduce file size
cur.execute("VACUUM;")
conn.commit()

# Reindex database to reduce file size
cur.execute("REINDEX;")
conn.commit()

optimized_db_size = os.path.getsize("cache.sqlite3")
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
df_sorted.to_csv("BasicOrPreferredPartsList.csv", index=False, header=True)

conn.close()
