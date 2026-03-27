import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="1234"
)

# fetchall() - returns all rows as a list of tuples
def get_all_students():
    command = "SELECT * FROM students"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchall()

# fetchone() - returns the next single row
def get_one_student():
    command = "SELECT * FROM students"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchone()

# fetchmany(n) - returns the next n rows
def get_n_students(n):
    command = "SELECT * FROM students"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchmany(n)

# SELECT with WHERE and multiple conditions
def get_students_by_major_and_min_gpa(major, min_gpa):
    command = "SELECT * FROM students WHERE major = %s AND gpa >= %s"
    with conn.cursor() as cur:
        cur.execute(command, (major, min_gpa))
        return cur.fetchall()

# SELECT with ORDER BY
def get_students_ordered_by_gpa():
    command = "SELECT * FROM students ORDER BY gpa DESC"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchall()

# SELECT with LIKE - pattern matching
def search_students_by_name(pattern):
    command = "SELECT * FROM students WHERE name LIKE %s"
    with conn.cursor() as cur:
        cur.execute(command, (f"%{pattern}%",))
        return cur.fetchall()

# SELECT with LIMIT and OFFSET - useful for pagination
def get_students_paginated(limit, offset):
    command = "SELECT * FROM students ORDER BY id LIMIT %s OFFSET %s"
    with conn.cursor() as cur:
        cur.execute(command, (limit, offset))
        return cur.fetchall()


print("All:", get_all_students())
print("One:", get_one_student())
print("First 2:", get_n_students(2))
print("IS majors with GPA >= 3:", get_students_by_major_and_min_gpa('IS', 3.0))
print("Ordered by GPA:", get_students_ordered_by_gpa())
print("Name contains 'R':", search_students_by_name('R'))
print("Page 1 (2 per page):", get_students_paginated(2, 0))
print("Page 2 (2 per page):", get_students_paginated(2, 2))

conn.close()
