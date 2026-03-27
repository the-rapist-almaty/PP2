# psycopg2 is the most popular PostgreSQL adapter for Python
# It lets us send SQL commands to a PostgreSQL database from Python code
import psycopg2
import csv

# To do anything with the database, we first need a connection
# psycopg2.connect() opens a connection to an existing PostgreSQL server
# Parameters:
#   host     - where the server is running ("localhost" means this machine)
#   database - which database to connect to (default one is called "postgres")
#   user     - PostgreSQL username
#   password - password for that user
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="1234"
)

def create_table():
    # SQL command to create a new table called "students"
    # Each column has a name and a data type:
    #   id      - SERIAL means auto-incrementing integer (1, 2, 3, ...)
    #   PRIMARY KEY means this column uniquely identifies each row
    #   name    - VARCHAR(255) is a string up to 255 characters
    #   major   - VARCHAR(10) is a string up to 10 characters
    #   gpa     - NUMERIC stores decimal numbers (e.g. 3.75)
    #   year    - INTEGER stores whole numbers
    command = """CREATE TABLE students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                major VARCHAR(10),
                gpa NUMERIC,
                year INTEGER
            )"""

    # conn.cursor() creates a cursor - an object that executes SQL commands
    # "with ... as cur" ensures the cursor is closed automatically when done
    with conn.cursor() as cur:
        cur.execute(command)
        # conn.commit() saves (commits) the changes to the database
        # Without commit, the changes would be lost when the connection closes
        conn.commit()

def insert_student(name, major, gpa, year):
    # %s is a placeholder - psycopg2 safely substitutes the actual values
    # NEVER use f-strings or string concatenation for SQL values!
    # That would make your code vulnerable to SQL injection attacks
    command = """INSERT INTO students(name, major, gpa, year) VALUES(%s, %s, %s, %s)"""

    with conn.cursor() as cur:
        # The second argument to execute() is a tuple of values
        # that replace the %s placeholders, in order
        cur.execute(command, (name, major, gpa, year))
        conn.commit()

def insert_student_from_csv(csv_file_name):
    command = "INSERT INTO students(name, major, gpa, year) VALUES(%s, %s, %s, %s)"

    with conn.cursor() as cur:
        with open(csv_file_name, "r") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            _ = next(csvreader)  # skip the header row (name, major, gpa, year)
            for row in csvreader:
                name, major, gpa, year = row
                cur.execute(command, (name, major, gpa, year))
        # commit once after all rows are inserted (more efficient than
        # committing after each row - fewer round-trips to the database)
        conn.commit()

def get_students_filter_by_gpa(gpa):
    command = "SELECT * FROM students WHERE gpa > %s"
    with conn.cursor() as cur:
        # When passing a single parameter, it must still be a tuple
        # (gpa,) is a tuple with one element
        # (gpa) without the comma is just parentheses, not a tuple!
        cur.execute(command, (gpa,))
        # fetchall() returns all matching rows as a list of tuples
        # Each tuple is one row: (id, name, major, gpa, year)
        return cur.fetchall()

# Uncomment these one by one to run them:
# create_table()
# insert_student('Raimbek Gosling', 'IS', 5.0, 1)
# insert_student_from_csv('students.csv')

gpa = float(input("Enter minimum GPA: "))
print(get_students_filter_by_gpa(gpa))

# Always close the connection when done to free up database resources
conn.close()
