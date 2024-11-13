![CSV File Preview](/images/CSV.avif)

# JLCPCB Parts Database

This repository processes the massive SQLite database from [yaqwsx/jlcparts](https://github.com/yaqwsx/jlcparts) into two convenient files.


### Files

* **Basic and Preferred Parts CSV**: A lightweight (~3MB) CSV file containing basic and preferred parts information.
* **In-Stock Components SQLite Database**: A filtered SQLite database (~1GB) containing only components with five or more items in stock.


### Why

The original database is a massive 10GB multi-volume zip archive, unsupported by most zip libraries due to its use of an older part of the zip standard. This repository simplifies access to the data by providing smaller, more manageable files.


### Automatically Updated Files

Both files are automatically updated using GitHub Actions and hosted on GitHub Pages:


* [Basic and Preferred Parts CSV](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv)
* [In-Stock Components SQLite Database](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components.sqlite3)


### Example Usage

Check out the included Jupyter Notebook `sqlite-search.ipynb` for an example of how to download the database and perform a basic search on the SQLite database using a SQLite query. For CSV files, consider using the pandas library for Python.


### Contributions

Feel free to contribute to this repository by reporting issues, suggesting improvements, or adding new features!


## How it Works


This repository uses a GitHub Actions workflow (`.github/workflows/sync-db.yml`) to automatically update the parts database, running on a default Ubuntu image. Here's a step-by-step explanation of the process:


### Steps


1. **Trigger**
	* The workflow triggers daily at 6:00 AM UTC, three hours after yaqwsx/jlcparts updates their database, on code commit, or manually using the "Run workflow" button.


2. **Download Database**
	* The workflow downloads the latest JLCPCB parts database zip volumes from https://github.com/yaqwsx/jlcparts.


3. **Extract Database**
	* The workflow extracts the database files using 7zip, one of the few modern implementations supporting zip volumes.


4. **Run Python Script**
	* The workflow runs the `generate-database.py` script, which:
		- Renames the database file.
		- Deletes components with low stock (<5).
		- Creates an FTS (Full-Text Search) index for faster searching.
		- Reindexes and vacuums the database to reduce file size.
		- Retrieves basic/preferred components and saves them to a CSV file using pandas.


5. **Upload Artifact**
	* The workflow uploads the updated database files as a GitHub Pages artifact.


6. **Deploy**
	* The workflow deploys the updated database files to the GitHub Pages environment.

