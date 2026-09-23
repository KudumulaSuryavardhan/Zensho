from database.database import get_db_connection
from werkzeug.security import generate_password_hash


email = "kudumulasuryavardhan@gmail.com"
password = "Sai Surya"


conn = get_db_connection()

password_hash = generate_password_hash(password)


user = conn.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)
).fetchone()


if user:

    conn.execute(
        """
        UPDATE users
        SET password = ?, role = 'admin'
        WHERE email = ?
        """,
        (password_hash, email)
    )

    print("Existing account converted to ADMIN.")

else:

    conn.execute(
        """
        INSERT INTO users
        (name, email, password, role)
        VALUES (?, ?, ?, ?)
        """,
        (
            "Zensho Admin",
            email,
            password_hash,
            "admin"
        )
    )

    print("New ADMIN account created.")


conn.commit()
conn.close()