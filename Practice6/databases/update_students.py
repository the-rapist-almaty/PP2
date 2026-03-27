import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="1234"
)

# UPDATE a single field by id
def update_student_gpa(student_id, new_gpa):
    command = "UPDATE students SET gpa = %s WHERE id = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_gpa, student_id))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

# UPDATE multiple fields at once
def update_student(student_id, name, major, gpa, year):
    command = """UPDATE students
                 SET name = %s, major = %s, gpa = %s, year = %s
                 WHERE id = %s"""
    with conn.cursor() as cur:
        cur.execute(command, (name, major, gpa, year, student_id))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

# UPDATE by name instead of id
def update_major_by_name(student_name, new_major):
    command = "UPDATE students SET major = %s WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_major, student_name))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

# UPDATE with a condition - e.g., increment year for all students with GPA above threshold
def promote_high_gpa_students(min_gpa):
    command = "UPDATE students SET year = year + 1 WHERE gpa >= %s"
    with conn.cursor() as cur:
        cur.execute(command, (min_gpa,))
        conn.commit()
        print(f"Promoted {cur.rowcount} student(s)")


# update_student_gpa(1, 4.5)
# update_student(1, '', '', 4.5, 2)
# update_major_by_name('', '')
# promote_high_gpa_students(3.0)

conn.close()
