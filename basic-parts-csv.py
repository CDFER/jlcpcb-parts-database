import pandas as pd
import sqlite3
import os

# TODO Exclude 0201 components?

output_directory = "db_build"
os.chdir(output_directory)

conn = sqlite3.connect("cache.sqlite3")
cur = conn.cursor()
cur.execute("DELETE FROM components WHERE stock <= 0;")
conn.commit()
print(f"Deleted {cur.rowcount} components that aren't in stock")

cur = conn.cursor()
cur.execute(
    "SELECT * FROM v_components WHERE (basic > 0 OR preferred > 0) AND stock >= 10;"
)
filtered_components = cur.fetchall()

df = pd.DataFrame(filtered_components, columns=[desc[0] for desc in cur.description])
df_sorted = df.sort_values(by=["category", "subcategory"])
df_sorted.to_csv(
    "BasicOrPreferredPartsList.csv", index=False, header=True
)

conn.close()
