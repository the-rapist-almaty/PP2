"""
TSIS1 — Extended PhoneBook
"""

import csv
import json
import os
from datetime import date, datetime
from connect import get_connection


#  HELPERS
def _print_table(rows):
    """Pretty-print a list of contact tuples."""
    if not rows:
        print("  (no results)")
        return
    header = f"{'ID':<5} {'Name':<18} {'Email':<25} {'Birthday':<12} {'Group':<10} {'Phones'}"
    print("\n" + header)
    print("─" * len(header))
    for r in rows:
        cid, name, email, bday, group, phones = r[0], r[1], r[2], r[3], r[4], r[5]
        print(
            f"{str(cid):<5} {str(name):<18} {str(email or ''):<25} "
            f"{str(bday or ''):<12} {str(group or ''):<10} {phones or ''}"
        )
    print()


def _get_group_id(cur, group_name: str) -> int:
    """Return group id; create group if it does not exist."""
    cur.execute("SELECT id FROM groups WHERE name = %s;", (group_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id;", (group_name,))
    return cur.fetchone()[0]


#  INSERT / UPSERT

def insert_from_console():
    """Collect contact details from the user and upsert into the database."""
    name     = input("First name: ").strip()
    email    = input("Email (Enter to skip): ").strip() or None
    birthday = input("Birthday YYYY-MM-DD (Enter to skip): ").strip() or None
    group    = input("Group (Family/Work/Friend/Other) [Other]: ").strip() or "Other"

    phones = []
    print("Enter phone numbers (leave name blank to finish):")
    while True:
        phone = input("  Phone number (blank to stop): ").strip()
        if not phone:
            break
        ptype = input("  Type (home/work/mobile) [mobile]: ").strip() or "mobile"
        phones.append((phone, ptype))

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # upsert contact
                cur.execute("CALL upsert_contact(%s, %s, %s, %s);",
                            (name, email, birthday, group))
                cur.execute("SELECT id FROM contacts WHERE first_name = %s LIMIT 1;", (name,))
                contact_id = cur.fetchone()[0]
                for phone, ptype in phones:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s) "
                        "ON CONFLICT DO NOTHING;",
                        (contact_id, phone, ptype)
                    )
        print(f"Contact '{name}' saved successfully.")
    finally:
        conn.close()


def insert_from_csv(filepath: str):
    """Import contacts from a CSV file with columns:
    first_name, phone, type, email, birthday, group
    """
    conn = get_connection()
    inserted = skipped = 0
    try:
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name     = row.get("first_name", "").strip()
                phone    = row.get("phone", "").strip()
                ptype    = row.get("type", "mobile").strip() or "mobile"
                email    = row.get("email", "").strip() or None
                birthday = row.get("birthday", "").strip() or None
                group    = row.get("group", "Other").strip() or "Other"

                if not name:
                    skipped += 1
                    continue

                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("CALL upsert_contact(%s, %s, %s, %s);",
                                        (name, email, birthday, group))
                            cur.execute("SELECT id FROM contacts WHERE first_name = %s LIMIT 1;", (name,))
                            cid = cur.fetchone()[0]
                            if phone:
                                cur.execute(
                                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s) "
                                    "ON CONFLICT DO NOTHING;",
                                    (cid, phone, ptype)
                                )
                    inserted += 1
                except Exception as e:
                    print(f"  Skipping row ({name}): {e}")
                    skipped += 1
    finally:
        conn.close()
    print(f"CSV import: {inserted} inserted/updated, {skipped} skipped.")


#  SEARCH / FILTER

def search_all(query: str):
    """Full-text search across name, email, and all phone numbers."""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s);", (query,))
            rows = cur.fetchall()
    conn.close()
    print(f"\nSearch results for '{query}':")
    _print_table(rows)


def filter_by_group():
    """Show contacts belonging to a chosen group."""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM groups ORDER BY name;")
            groups = [r[0] for r in cur.fetchall()]

    print("\nAvailable groups:", ", ".join(groups))
    chosen = input("Enter group name: ").strip()

    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.first_name, c.email, c.birthday, g.name,
                       STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                WHERE g.name ILIKE %s
                GROUP BY c.id, c.first_name, c.email, c.birthday, g.name
                ORDER BY c.first_name;
            """, (chosen,))
            rows = cur.fetchall()
    conn.close()
    print(f"\nContacts in group '{chosen}':")
    _print_table(rows)


def search_by_email():
    """Search contacts by partial email match."""
    pattern = input("Enter email pattern (e.g. 'gmail'): ").strip()
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.first_name, c.email, c.birthday, g.name,
                       STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                WHERE c.email ILIKE %s
                GROUP BY c.id, c.first_name, c.email, c.birthday, g.name
                ORDER BY c.first_name;
            """, (f"%{pattern}%",))
            rows = cur.fetchall()
    conn.close()
    print(f"\nContacts matching email '{pattern}':")
    _print_table(rows)


#  PAGINATED NAVIGATION

def browse_paginated():
    """Navigate all contacts page by page with next/prev/quit."""
    print("\nSort by: 1=Name  2=Birthday  3=Date added")
    sort_choice = input("Choice [1]: ").strip()
    sort_map = {"1": "name", "2": "birthday", "3": "date"}
    sort = sort_map.get(sort_choice, "name")

    page_size = 5
    offset    = 0

    while True:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_contacts_paginated(%s, %s, %s);",
                            (page_size, offset, sort))
                rows = cur.fetchall()
                cur.execute("SELECT COUNT(*) FROM contacts;")
                total = cur.fetchone()[0]
        conn.close()

        page = offset // page_size + 1
        total_pages = max(1, (total + page_size - 1) // page_size)
        print(f"\n── Page {page}/{total_pages} (sorted by {sort}) ──")
        # get_contacts_paginated returns 7 cols; drop created_at for display
        display = [r[:6] for r in rows]
        _print_table(display)

        print("Commands: n=next  p=prev  q=quit")
        cmd = input(">> ").strip().lower()
        if cmd == "n":
            if offset + page_size < total:
                offset += page_size
            else:
                print("Already on the last page.")
        elif cmd == "p":
            if offset > 0:
                offset -= page_size
            else:
                print("Already on the first page.")
        elif cmd == "q":
            break


#  UPDATE

def add_phone_to_contact():
    """Add a phone number to an existing contact (calls add_phone procedure)."""
    name  = input("Contact name: ").strip()
    phone = input("New phone number: ").strip()
    ptype = input("Type (home/work/mobile) [mobile]: ").strip() or "mobile"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("CALL add_phone(%s, %s, %s);", (name, phone, ptype))
        print("Phone added.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def move_contact_to_group():
    """Move a contact to a different group (calls move_to_group procedure)."""
    name  = input("Contact name: ").strip()
    group = input("Target group name: ").strip()
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("CALL move_to_group(%s, %s);", (name, group))
        print(f"Moved '{name}' to group '{group}'.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


#  DELETE

def delete_contact():
    """Delete a contact by name or phone (calls delete_contact procedure)."""
    print("Delete by: 1=Name  2=Phone")
    choice = input("Choice: ").strip()
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                if choice == "1":
                    name = input("Contact name: ").strip()
                    cur.execute("CALL delete_contact(%s, NULL);", (name,))
                    print("Deleted by name.")
                elif choice == "2":
                    phone = input("Phone number: ").strip()
                    cur.execute("CALL delete_contact(NULL, %s);", (phone,))
                    print("Deleted by phone.")
                else:
                    print("Invalid choice.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


#  JSON EXPORT / IMPORT

def export_to_json():
    """Export all contacts (with phones and group) to a JSON file."""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.first_name, c.email,
                       c.birthday::text, g.name AS group_name,
                       c.created_at::text
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.id;
            """)
            contacts = cur.fetchall()

            result = []
            for row in contacts:
                cid = row[0]
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s;", (cid,)
                )
                phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]
                result.append({
                    "id":         cid,
                    "first_name": row[1],
                    "email":      row[2],
                    "birthday":   row[3],
                    "group":      row[4],
                    "created_at": row[5],
                    "phones":     phones
                })
    conn.close()

    filename = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(result)} contacts to '{filename}'.")


def import_from_json():
    """Import contacts from a JSON file; ask user on duplicates."""
    filepath = input("Enter JSON file path: ").strip()
    if not os.path.exists(filepath):
        print("File not found.")
        return

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    inserted = skipped = overwritten = 0

    for entry in data:
        name     = entry.get("first_name", "").strip()
        email    = entry.get("email")
        birthday = entry.get("birthday")
        group    = entry.get("group") or "Other"
        phones   = entry.get("phones", [])

        if not name:
            skipped += 1
            continue

        # Check duplicate
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contacts WHERE first_name = %s LIMIT 1;", (name,))
            existing = cur.fetchone()

        if existing:
            ans = input(f"Contact '{name}' already exists. Overwrite? (y/n): ").strip().lower()
            if ans != "y":
                skipped += 1
                continue
            overwritten += 1
        else:
            inserted += 1

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("CALL upsert_contact(%s, %s, %s, %s);",
                                (name, email, birthday, group))
                    cur.execute("SELECT id FROM contacts WHERE first_name = %s LIMIT 1;", (name,))
                    cid = cur.fetchone()[0]
                    for p in phones:
                        cur.execute(
                            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s) "
                            "ON CONFLICT DO NOTHING;",
                            (cid, p.get("phone"), p.get("type", "mobile"))
                        )
        except Exception as e:
            print(f"  Error importing '{name}': {e}")

    conn.close()
    print(f"JSON import done: {inserted} new, {overwritten} overwritten, {skipped} skipped.")


#  MENU

MENU = """
╔══════════════════════════════════╗
║       PhoneBook  (TSIS1)         ║
╠══════════════════════════════════╣
║  1. Browse contacts (paginated)  ║
║  2. Search (name / email / phone)║
║  3. Filter by group              ║
║  4. Search by email              ║
║  5. Add contact (console)        ║
║  6. Import from CSV              ║
║  7. Import from JSON             ║
║  8. Export to JSON               ║
║  9. Add phone to contact         ║
║ 10. Move contact to group        ║
║ 11. Delete contact               ║
║  0. Exit                         ║
╚══════════════════════════════════╝"""


def main():
    print(MENU)
    while True:
        choice = input("\nOption: ").strip()
        if   choice == "1":  browse_paginated()
        elif choice == "2":
            q = input("Search query: ").strip()
            search_all(q)
        elif choice == "3":  filter_by_group()
        elif choice == "4":  search_by_email()
        elif choice == "5":  insert_from_console()
        elif choice == "6":
            path = input("CSV path [contacts.csv]: ").strip() or "contacts.csv"
            insert_from_csv(path)
        elif choice == "7":  import_from_json()
        elif choice == "8":  export_to_json()
        elif choice == "9":  add_phone_to_contact()
        elif choice == "10": move_contact_to_group()
        elif choice == "11": delete_contact()
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("Invalid option.")
        print(MENU)


if __name__ == "__main__":
    main()
