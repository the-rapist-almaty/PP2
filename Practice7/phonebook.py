import psycopg2
import csv
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# --- Connection ---

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# --- Table setup ---

def create_table():
    command = """CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL
            )"""
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()

# --- INSERT ---

def insert_contact(name, phone):
    command = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"
    with conn.cursor() as cur:
        cur.execute(command, (name, phone))
        conn.commit()

def insert_from_console():
    name = input("Enter name: ")
    phone = input("Enter phone: ")
    insert_contact(name, phone)
    print(f"Added: {name} - {phone}")

def insert_from_csv(csv_file):
    command = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"
    with conn.cursor() as cur:
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                name, phone = row
                cur.execute(command, (name, phone))
        conn.commit()
    print(f"Imported contacts from {csv_file}")

# --- SELECT ---

def get_all_contacts():
    command = "SELECT * FROM contacts ORDER BY name"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchall()

def search_contacts(pattern):
    command = "SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s"
    like_pattern = f"%{pattern}%"
    with conn.cursor() as cur:
        cur.execute(command, (like_pattern, like_pattern))
        return cur.fetchall()

# --- UPDATE ---

def update_phone(name, new_phone):
    command = "UPDATE contacts SET phone = %s WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_phone, name))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

def update_name(phone, new_name):
    command = "UPDATE contacts SET name = %s WHERE phone = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_name, phone))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

# --- DELETE ---

def delete_by_name(name):
    command = "DELETE FROM contacts WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (name,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

def delete_by_phone(phone):
    command = "DELETE FROM contacts WHERE phone = %s"
    with conn.cursor() as cur:
        cur.execute(command, (phone,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

# --- Main menu ---

def print_contacts(contacts):
    # print(contacts)       # a list of tuples (each tuple represents 1 row, each element in a tuple represents 1 column)
    # print(type(contacts)) # <class 'list'>

    if not contacts:
        print("  (no contacts)")
        return
    for c in contacts:
        print(f"  [{c[0]}] {c[1]} - {c[2]}")

def main():
    create_table()

    while True:
        print("\n--- PhoneBook ---")
        print("1. Show all contacts")
        print("2. Add contact (console)")
        print("3. Import from CSV")
        print("4. Search")
        print("5. Update phone by name")
        print("6. Update name by phone")
        print("7. Delete by name")
        print("8. Delete by phone")
        print("0. Exit")

        choice = input("\nChoice: ")

        if choice == "1":
            print_contacts(get_all_contacts())
        elif choice == "2":
            insert_from_console()
        elif choice == "3":
            filename = input("CSV file path: ")
            insert_from_csv(filename)
        elif choice == "4":
            pattern = input("Search: ")
            print_contacts(search_contacts(pattern))
        elif choice == "5":
            name = input("Name: ")
            new_phone = input("New phone: ")
            update_phone(name, new_phone)
        elif choice == "6":
            phone = input("Phone: ")
            new_name = input("New name: ")
            update_name(phone, new_name)
        elif choice == "7":
            name = input("Name: ")
            delete_by_name(name)
        elif choice == "8":
            phone = input("Phone: ")
            delete_by_phone(phone)
        elif choice == "0":
            break
        else:
            print("Invalid choice")

    conn.close()
    print("Goodbye!")

if __name__ == "__main__":
    main()
