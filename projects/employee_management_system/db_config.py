
import oracledb

DB_CONFIG = {
    "user":     "system",
    "password": "1234",
    "dsn":      "localhost:1521/XEPDB1",   
}



def get_connection():
    return oracledb.connect(**DB_CONFIG)


def initialize_database():
    ddl_statements = [
        """
        CREATE TABLE departments (
            dept_id    NUMBER PRIMARY KEY,
            dept_name  VARCHAR2(100) NOT NULL,
            location   VARCHAR2(100)
        )
        """,
        """
        CREATE SEQUENCE dept_seq START WITH 1 INCREMENT BY 1 NOCACHE
        """,
        """
        CREATE OR REPLACE TRIGGER dept_bir
        BEFORE INSERT ON departments
        FOR EACH ROW
        BEGIN
            IF :NEW.dept_id IS NULL THEN
                SELECT dept_seq.NEXTVAL INTO :NEW.dept_id FROM dual;
            END IF;
        END;
        """,

        
        """
        CREATE TABLE employees (
            emp_id      NUMBER PRIMARY KEY,
            first_name  VARCHAR2(50)  NOT NULL,
            last_name   VARCHAR2(50)  NOT NULL,
            email       VARCHAR2(100) UNIQUE NOT NULL,
            phone       VARCHAR2(20),
            hire_date   DATE          DEFAULT SYSDATE NOT NULL,
            job_title   VARCHAR2(100),
            salary      NUMBER(10, 2),
            dept_id     NUMBER REFERENCES departments(dept_id),
            status      VARCHAR2(10)  DEFAULT 'ACTIVE'
                            CHECK (status IN ('ACTIVE', 'INACTIVE'))
        )
        """,
        """
        CREATE SEQUENCE emp_seq START WITH 1001 INCREMENT BY 1 NOCACHE
        """,
        """
        CREATE OR REPLACE TRIGGER emp_bir
        BEFORE INSERT ON employees
        FOR EACH ROW
        BEGIN
            IF :NEW.emp_id IS NULL THEN
                SELECT emp_seq.NEXTVAL INTO :NEW.emp_id FROM dual;
            END IF;
        END;
        """,

        """
        CREATE TABLE emp_audit (
            audit_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            emp_id      NUMBER,
            action      VARCHAR2(10),
            changed_at  TIMESTAMP DEFAULT SYSTIMESTAMP,
            changed_by  VARCHAR2(50)
        )
        """,

        # ── Seed departments ─────────────────────────────────────────────────
        "INSERT INTO departments (dept_name, location) VALUES ('Human Resources', 'New York')",
        "INSERT INTO departments (dept_name, location) VALUES ('Engineering',     'San Francisco')",
        "INSERT INTO departments (dept_name, location) VALUES ('Finance',         'Chicago')",
        "INSERT INTO departments (dept_name, location) VALUES ('Marketing',       'Los Angeles')",
        "INSERT INTO departments (dept_name, location) VALUES ('Operations',      'Dallas')",
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for stmt in ddl_statements:
                try:
                    cur.execute(stmt)
                    conn.commit()
                except oracledb.DatabaseError as e:
                    err, = e.args
                    # ORA-00955: name already used – silently skip
                    if err.code not in (955, 2260, 1430):
                        print(f"[WARN] {err.message.strip()}")
    print(" Database initialized successfully.")
