
from datetime import date
from db_config import get_connection
def get_all_departments():
    sql = "SELECT dept_id, dept_name, location FROM departments ORDER BY dept_id"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_department_by_id(dept_id):
    sql = "SELECT dept_id, dept_name, location FROM departments WHERE dept_id = :1"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [dept_id])
            row = cur.fetchone()
            if row:
                cols = [c[0].lower() for c in cur.description]
                return dict(zip(cols, row))
    return None


def add_department(dept_name, location):
    sql = "INSERT INTO departments (dept_name, location) VALUES (:1, :2)"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [dept_name, location])
            conn.commit()
    print(f"  Department '{dept_name}' added.")


 

_EMP_SELECT = """
    SELECT e.emp_id, e.first_name, e.last_name, e.email, e.phone,
           e.hire_date, e.job_title, e.salary, e.dept_id,
           d.dept_name, e.status
    FROM   employees e
    LEFT JOIN departments d ON e.dept_id = d.dept_id
"""


def _rows_to_dicts(cur):
    cols = [c[0].lower() for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]



def add_employee(first_name, last_name, email, phone,
                 job_title, salary, dept_id,
                 hire_date=None):
    if hire_date is None:
        hire_date = date.today()

    sql = """
        INSERT INTO employees
            (first_name, last_name, email, phone, hire_date,
             job_title,  salary,    dept_id)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [first_name, last_name, email, phone,
                              hire_date, job_title, salary, dept_id])
            
            cur.execute(
                "INSERT INTO emp_audit(emp_id, action, changed_by) "
                "VALUES ((SELECT MAX(emp_id) FROM employees), 'INSERT', USER)",
            )
            conn.commit()
    print(f"  Employee '{first_name} {last_name}' added successfully.")



def get_all_employees(status="ACTIVE"):
    sql = _EMP_SELECT + " WHERE e.status = :1 ORDER BY e.emp_id"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [status])
            return _rows_to_dicts(cur)


def get_employee_by_id(emp_id):
    sql = _EMP_SELECT + " WHERE e.emp_id = :1"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [emp_id])
            row = cur.fetchone()
            if row:
                cols = [c[0].lower() for c in cur.description]
                return dict(zip(cols, row))
    return None


def search_employees(keyword):
    kw = f"%{keyword.upper()}%"
    sql = _EMP_SELECT + """
        WHERE UPPER(e.first_name) LIKE :1
           OR UPPER(e.last_name)  LIKE :1
           OR UPPER(e.email)      LIKE :1
           OR UPPER(e.job_title)  LIKE :1
        ORDER BY e.emp_id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [kw])
            return _rows_to_dicts(cur)


def get_employees_by_department(dept_id):
    sql = _EMP_SELECT + " WHERE e.dept_id = :1 AND e.status = 'ACTIVE' ORDER BY e.emp_id"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [dept_id])
            return _rows_to_dicts(cur)



def update_employee(emp_id, **kwargs):
    allowed = {"first_name", "last_name", "email", "phone",
               "job_title", "salary", "dept_id", "status"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        print("  Nothing to update.")
        return

    set_clause = ", ".join(f"{col} = :{i+1}" for i, col in enumerate(fields))
    values = list(fields.values()) + [emp_id]

    sql = f"UPDATE employees SET {set_clause} WHERE emp_id = :{len(values)}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
            if cur.rowcount == 0:
                print(f"  No employee found with ID {emp_id}.")
                return
            cur.execute(
                "INSERT INTO emp_audit(emp_id, action, changed_by) VALUES (:1, 'UPDATE', USER)",
                [emp_id],
            )
            conn.commit()
    print(f"  Employee {emp_id} updated.")


def update_salary(emp_id, new_salary):
    update_employee(emp_id, salary=new_salary)


def transfer_department(emp_id, new_dept_id):
    update_employee(emp_id, dept_id=new_dept_id)



def deactivate_employee(emp_id):
    sql = "UPDATE employees SET status = 'INACTIVE' WHERE emp_id = :1"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [emp_id])
            if cur.rowcount == 0:
                print(f"  No employee found with ID {emp_id}.")
                return
            cur.execute(
                "INSERT INTO emp_audit(emp_id, action, changed_by) VALUES (:1, 'DELETE', USER)",
                [emp_id],
            )
            conn.commit()
    print(f"  Employee {emp_id} deactivated.")


def delete_employee_permanent(emp_id):
    sql = "DELETE FROM employees WHERE emp_id = :1"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [emp_id])
            conn.commit()
    print(f"  Employee {emp_id} permanently deleted.")



def get_salary_report():
    sql = """
        SELECT d.dept_name,
               COUNT(e.emp_id)           AS headcount,
               ROUND(AVG(e.salary), 2)   AS avg_salary,
               MIN(e.salary)             AS min_salary,
               MAX(e.salary)             AS max_salary,
               SUM(e.salary)             AS total_payroll
        FROM   employees   e
        JOIN   departments d ON e.dept_id = d.dept_id
        WHERE  e.status = 'ACTIVE'
        GROUP  BY d.dept_name
        ORDER  BY total_payroll DESC
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return _rows_to_dicts(cur)


def get_audit_log(limit=20):
    sql = """
        SELECT a.audit_id, a.emp_id, e.first_name || ' ' || e.last_name AS emp_name,
               a.action, TO_CHAR(a.changed_at, 'YYYY-MM-DD HH24:MI:SS') AS changed_at,
               a.changed_by
        FROM   emp_audit  a
        LEFT JOIN employees e ON a.emp_id = e.emp_id
        ORDER  BY a.changed_at DESC
        FETCH  FIRST :1 ROWS ONLY
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [limit])
            return _rows_to_dicts(cur)
