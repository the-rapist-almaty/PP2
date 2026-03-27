import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="1234"
)

# DELETE by id
def delete_student_by_id(student_id):
    command = "DELETE FROM students WHERE id = %s"
    with conn.cursor() as cur:
        cur.execute(command, (student_id,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

# DELETE by name
def delete_student_by_name(name):
    command = "DELETE FROM students WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (name,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

# DELETE with a condition
def delete_students_below_gpa(min_gpa):
    command = "DELETE FROM students WHERE gpa < %s"
    with conn.cursor() as cur:
        cur.execute(command, (min_gpa,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

# DELETE all rows (clears the table but keeps the structure)
def delete_all_students():
    command = "DELETE FROM students"
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

# DROP TABLE - removes the table entirely (structure + data)
def drop_students_table():
    command = "DROP TABLE IF EXISTS students"
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()
        print("Table dropped")


# delete_student_by_id(1)
# delete_student_by_name('')
# delete_students_below_gpa(3.0)
# delete_all_students()
# drop_students_table()

conn.close()
