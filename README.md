# osint_phone_lookup
Your very own searchable phone database for phone numbers you have previously identified owners/users or come across in prior instances/sources/investigations.

Overview

This is a lightweight, local OSINT phone lookup tool built with Python and SQLite. It allows you to:
	•	Store and normalize phone numbers
	•	Link numbers to identities (name, alias, notes)
	•	Track sources of information
	•	Search by full or partial phone number
	•	Import and export data via CSV
No external database or dependencies are required.

Requirements
	•	Python 3.x installed
	•	No additional packages needed (uses built-in libraries)

Setup Instructions
	1	Create a folder (e.g., osint_phone_lookup)
	2	Save the script as main.py inside the folder
	3	Open a terminal in that folder
	4	Run the script:
python main.py
The database file (database.db) will be created automatically.

How to Use
When you run the script, you will see a menu:
1. Add Entry
2. Search
3. Import CSV
4. Export CSV
5. Exit


1 - Add Entry
Manually add a phone record:
	•	Enter phone number (any format)
	•	Add name, alias, notes
	•	Provide a source
	•	Set confidence level (low / med / high)
The system will automatically normalize the phone number.

2 - Search
	•	Enter a full or partial phone number
	•	Example:
	◦	9545551234
	◦	5551234
	•	Returns all matching records with associated identities and sources

3 - Import CSV
Bulk import phone data from a CSV file.
You will be prompted to enter the file path:
Enter CSV file path: data.csv

4 - Export CSV
Exports the entire database into a CSV file.
You will be prompted to enter an output path:
Enter output CSV file path: export.csv

5 - Bulk Search
Bulk search allows you to provide a text (Numbers.txt), with one number per line for a search of the database.
You will be prompted to enter the path of the input file.
You will be provided the option to print results to screen or export to .csv

CSV Format (IMPORTANT)
Your CSV file must include the following headers:
phone,name,alias,notes,source,confidence
Example CSV
phone,name,alias,notes,source,confidence
+19545551234,John Doe,jdoe,Forum post,Reddit,medium
954-555-9876,Jane Smith,,Leaked list,Breach dump,low
(305) 555-2222,Bob Lee,,Marketplace contact,Facebook,high

Field Descriptions
	•	phone: Required. Any format accepted (will be normalized automatically)
	•	name: Person’s name (optional)
	•	alias: Username or nickname (optional)
	•	notes: Context or details (optional)
	•	source: Where the data came from (recommended)
	•	confidence: low / med / high (defaults to "low" if missing)

Notes on Data Handling
	•	Phone numbers are normalized to a consistent format internally
	•	Duplicate phone numbers are automatically handled
	•	Multiple identities can be linked to the same number (expected in OSINT)
	•	All entries are stored locally in database.db

Best Practices
	•	Always include a source for credibility
	•	Use consistent confidence levels
	•	Clean your CSV before importing when possible
	•	Keep backups of your database file

Limitations
	•	No fuzzy name matching (yet)
	•	No web interface (CLI only)
	•	No automatic enrichment (carrier lookup, etc.)

Possible Future Enhancements
	•	Web interface (Flask-based UI)
	•	Graph visualization of relationships
	•	Fuzzy matching for identities
	•	API integrations for enrichment
	•	Filtered export (search-based export)

Security & Legal Reminder
Use this tool responsibly:
	•	Only store and process lawfully obtained data
	•	Be mindful of privacy laws and regulations
	•	Secure your database if it contains sensitive information

Support / Expansion
This system is intentionally simple and modular. It can be extended into:
	•	A full OSINT platform
	•	A link analysis tool
	•	A local intelligence database

