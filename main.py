import sqlite3
import re
import csv

DB_NAME = "database.db"

# --- Normalize phone number to E.164-like ---
def normalize_phone(phone):
    if not phone:
        return None

    phone = str(phone).strip()

    # Remove everything except digits
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None

    # US logic (adjust if international matters)
    if len(digits) == 10:
        return "+1" + digits
    elif len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    elif digits.startswith("1") and len(digits) > 11:
        return "+" + digits
    else:
        # fallback (keeps international numbers usable)
        return "+" + digits

# --- Initialize database ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Performance tweak
    c.execute("PRAGMA journal_mode = WAL;")

    c.execute("""
    CREATE TABLE IF NOT EXISTS phone_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        carrier TEXT,
        line_type TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        alias TEXT,
        notes TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        date_collected TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS links (
        phone_id INTEGER,
        identity_id INTEGER,
        source_id INTEGER,
        confidence TEXT,
        FOREIGN KEY(phone_id) REFERENCES phone_numbers(id),
        FOREIGN KEY(identity_id) REFERENCES identities(id),
        FOREIGN KEY(source_id) REFERENCES sources(id)
    )
    """)

    # Index for faster search
    c.execute("CREATE INDEX IF NOT EXISTS idx_phone ON phone_numbers(phone);")

    conn.commit()
    conn.close()


# --- Add single entry ---
def add_entry():
    phone = input("Phone number: ")
    phone = normalize_phone(phone)

    if not phone:
        print("Invalid phone number.\n")
        return

    name = input("Name: ")
    alias = input("Alias: ")
    notes = input("Notes: ")
    source = input("Source: ")
    confidence = input("Confidence (low/med/high): ")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Insert phone
    c.execute("INSERT OR IGNORE INTO phone_numbers (phone) VALUES (?)", (phone,))
    c.execute("SELECT id FROM phone_numbers WHERE phone=?", (phone,))
    phone_id = c.fetchone()[0]

    # Insert identity
    c.execute(
        "INSERT INTO identities (name, alias, notes) VALUES (?, ?, ?)",
        (name, alias, notes)
    )
    identity_id = c.lastrowid

    # Insert source
    c.execute(
        "INSERT INTO sources (source, date_collected) VALUES (?, datetime('now'))",
        (source,)
    )
    source_id = c.lastrowid

    # Link everything
    c.execute(
        "INSERT INTO links (phone_id, identity_id, source_id, confidence) VALUES (?, ?, ?, ?)",
        (phone_id, identity_id, source_id, confidence)
    )

    conn.commit()
    conn.close()

    print("✔ Entry added.\n")


# --- Search ---
def search():
    query = input("Enter phone (full or partial): ")
    query = query.replace("+", "").strip()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT phone_numbers.phone, identities.name, identities.alias,
           identities.notes, sources.source, links.confidence
    FROM phone_numbers
    JOIN links ON phone_numbers.id = links.phone_id
    JOIN identities ON identities.id = links.identity_id
    JOIN sources ON sources.id = links.source_id
    WHERE phone_numbers.phone LIKE ?
    """, ('%' + query + '%',))

    results = c.fetchall()
    conn.close()

    if results:
        for r in results:
            print(f"""
Phone: {r[0]}
Name: {r[1]}
Alias: {r[2]}
Notes: {r[3]}
Source: {r[4]}
Confidence: {r[5]}
---------------------------
""")
    else:
        print("No results found.\n")


# --- CSV IMPORT ---
def import_csv():
    file_path = input("Enter CSV file path: ").strip().strip('"')

    import os
    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}\n")
        return

    imported = 0
    skipped = 0

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                # --- CLEAN KEYS (handles PHONE, Phone , phone etc.) ---
                row = {
                    (k or "").strip().lower(): (v or "").strip()
                    for k, v in row.items()
                }

                raw_phone = row.get("phone")

                if not raw_phone:
                    skipped += 1
                    continue

                phone = normalize_phone(raw_phone)

                if not phone:
                    skipped += 1
                    continue

                name = row.get("name", "")
                alias = row.get("alias", "")
                notes = row.get("notes", "")
                source = row.get("source", "")
                confidence = row.get("confidence", "low")

                try:
                    # Insert phone
                    c.execute(
                        "INSERT OR IGNORE INTO phone_numbers (phone) VALUES (?)",
                        (phone,)
                    )
                    c.execute(
                        "SELECT id FROM phone_numbers WHERE phone=?",
                        (phone,)
                    )
                    phone_row = c.fetchone()

                    if not phone_row:
                        skipped += 1
                        continue

                    phone_id = phone_row[0]

                    # Insert identity
                    c.execute(
                        "INSERT INTO identities (name, alias, notes) VALUES (?, ?, ?)",
                        (name, alias, notes)
                    )
                    identity_id = c.lastrowid

                    # Insert source
                    c.execute(
                        "INSERT INTO sources (source, date_collected) VALUES (?, datetime('now'))",
                        (source,)
                    )
                    source_id = c.lastrowid

                    # Link
                    c.execute("""
                        INSERT INTO links (phone_id, identity_id, source_id, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (phone_id, identity_id, source_id, confidence))

                    imported += 1

                except Exception:
                    skipped += 1
                    continue

        conn.commit()

    except Exception as e:
        print(f"❌ Import error: {e}\n")

    finally:
        conn.close()

    print("\n📊 IMPORT SUMMARY")
    print(f"✔ Imported: {imported}")
    print(f"⚠ Skipped:  {skipped}\n")

# --- CSV EXPORT ---
def export_csv():
    file_path = input("Enter output CSV file path: ")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT phone_numbers.phone, identities.name, identities.alias,
           identities.notes, sources.source, links.confidence
    FROM phone_numbers
    JOIN links ON phone_numbers.id = links.phone_id
    JOIN identities ON identities.id = links.identity_id
    JOIN sources ON sources.id = links.source_id
    """)

    rows = c.fetchall()
    conn.close()

    try:
        with open(file_path, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["phone", "name", "alias", "notes", "source", "confidence"])

            for row in rows:
                writer.writerow(row)

        print(f"✔ Exported {len(rows)} records to {file_path}\n")

    except Exception as e:
        print(f"Error exporting CSV: {e}\n")

# --- Bulk Search ---

def bulk_search():
    import os

    file_path = input("Enter path to text file: ").strip().strip('"')

    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}\n")
        return

    export_choice = input("Export results to CSV? (y/n): ").lower().strip()
    export_file = None

    if export_choice == "y":
        export_file = input("Enter output CSV file path: ").strip().strip('"')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    found = 0
    not_found = 0
    skipped = 0
    results_to_export = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            raw = line.strip()

            if not raw:
                skipped += 1
                continue

            phone = normalize_phone(raw)

            if not phone:
                skipped += 1
                continue

            c.execute("""
            SELECT phone_numbers.phone, identities.name, identities.alias,
                   identities.notes, sources.source, links.confidence
            FROM phone_numbers
            JOIN links ON phone_numbers.id = links.phone_id
            JOIN identities ON identities.id = links.identity_id
            JOIN sources ON sources.id = links.source_id
            WHERE phone_numbers.phone = ?
               OR phone_numbers.phone LIKE ?
            """, (phone, '%' + phone[-10:]))

            rows = c.fetchall()

            if rows:
                found += 1
                print(f"\n📞 {phone} FOUND:")
                for r in rows:
                    print(f"  Name: {r[1]} | Alias: {r[2]} | Source: {r[4]} | Confidence: {r[5]}")

                    if export_file:
                        results_to_export.append(r)
            else:
                not_found += 1

    except Exception as e:
        print(f"❌ Error during bulk search: {e}")
        conn.close()
        return

    conn.close()

    # --- Export if requested ---
    if export_file and results_to_export:
        try:
            with open(export_file, "w", newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["phone", "name", "alias", "notes", "source", "confidence"])

                for row in results_to_export:
                    writer.writerow(row)

            print(f"\n✔ Results exported to {export_file}")
        except Exception as e:
            print(f"❌ Export error: {e}")

    # --- Summary ---
    print("\n📊 BULK SEARCH SUMMARY")
    print(f"✔ Found:      {found}")
    print(f"❌ Not Found: {not_found}")
    print(f"⚠ Skipped:   {skipped}\n")



# --- Menu ---
def menu():
    while True:
        print("""
1. Add Entry
2. Search
3. Import CSV
4. Export CSV
5. Bulk Search (from file)
6. Exit
""")
        choice = input("Select: ")

        if choice == "1":
            add_entry()
        elif choice == "2":
            search()
        elif choice == "3":
            import_csv()
        elif choice == "4":
            export_csv()
        elif choice == "5":
            bulk_search()
        elif choice == "6":
            break
        else:
            print("Invalid option\n")


# --- Run ---
if __name__ == "__main__":
    init_db()
    menu()
