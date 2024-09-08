import pandas as pd
import sqlite3
import os

def calculate_database_space(db_file):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Get the page size and count
    cur.execute("PRAGMA page_size")
    page_size = cur.fetchone()[0]
    cur.execute("PRAGMA page_count")
    page_count = cur.fetchone()[0]

    # Calculate the used space
    used_size = page_size * page_count

    # Get the file size
    file_size = os.path.getsize(db_file)

    # Calculate the empty space
    empty_space = file_size - used_size

    # Close the connection
    conn.close()

    # Return the results as a dictionary
    return {
        "used_space_mb": used_size / (1024**2),
        "file_size_mb": file_size / (1024**2),
        "empty_space_mb": empty_space / (1024**2),
    }


os.chdir("db_build")

os.rename("cache.sqlite3", "jlcpcb-components.sqlite3")

initial_db_size = os.path.getsize("jlcpcb-components.sqlite3")
print(f"Initial SQLite Database Size: {initial_db_size / (1024 ** 3):.2f} GiB")
print(calculate_database_space("jlcpcb-components.sqlite3"))

conn = sqlite3.connect("jlcpcb-components.sqlite3")
cur = conn.cursor()

# Delete components with low stock
cur.execute("DELETE FROM components WHERE stock < 5;")
conn.commit()
print(f"Deleted {cur.rowcount} components with low stock")
print(calculate_database_space("jlcpcb-components.sqlite3"))

# Create an FTS (Full-Text Search) index on multiple columns
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
print(calculate_database_space("jlcpcb-components.sqlite3"))

# Reindex database to reduce file size
cur.execute("REINDEX;")
conn.commit()

# Vacuum database to reduce file size
cur.execute("VACUUM;")
conn.commit()

optimized_db_size = os.path.getsize("jlcpcb-components.sqlite3")
print(f"Optimized Database Size: {optimized_db_size / (1024 ** 3):.2f} GiB")
print(calculate_database_space("jlcpcb-components.sqlite3"))

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

conn.close()
