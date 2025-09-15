import pymysql

# Connect to MySQL server (without specifying database)
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='Akashdhoni11',
    port=3306
)

# Create database if it doesn't exist
with conn.cursor() as cursor:
    cursor.execute("CREATE DATABASE IF NOT EXISTS test")

conn.close()

# Connect to the database
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='Akashdhoni11',
    database='test',
    port=3306
)

# Create users table if it doesn't exist
with conn.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            age INT
        )
    """)

    # Insert sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO users (name, email, age) VALUES (%s, %s, %s)
        """, [
            ('Alice Johnson', 'alice@example.com', 30),
            ('Bob Smith', 'bob@example.com', 25),
            ('Charlie Brown', 'charlie@example.com', 35)
        ])

conn.commit()
conn.close()
print("Database 'test' and table 'users' created or already exist. Sample data inserted.")
