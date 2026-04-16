
import sys
from datetime import datetime

from db_config import initialize_database
import employee_model as em

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    G  = Fore.GREEN;  R = Fore.RED;  Y = Fore.YELLOW
    C  = Fore.CYAN;   B = Fore.BLUE; M = Fore.MAGENTA
    W  = Style.BRIGHT; RST = Style.RESET_ALL
except ImportError:
    G = R = Y = C = B = M = W = RST = ""


def banner():
    print(f"""
{W}{B}╔══════════════════════════════════════════════════════╗
║       EMPLOYEE  MANAGEMENT  SYSTEM      ║
╚══════════════════════════════════════════════════════╝{RST}
""")


def separator(char="─", width=55):
    print(C + char * width + RST)


def print_employees(employees):
    if not employees:
        print(Y + "  No records found." + RST)
        return
    separator()
    header = f"{'ID':<6} {'Name':<25} {'Job Title':<22} {'Dept':<18} {'Salary':>10}"
    print(W + header + RST)
    separator()
    for e in employees:
        name  = f"{e['first_name']} {e['last_name']}"
        dept  = e.get('dept_name') or "—"
        sal   = f"${e['salary']:,.2f}" if e['salary'] else "—"
        status_tag = "" if e.get("status") == "ACTIVE" else f" {R}[INACTIVE]{RST}"
        print(f"{e['emp_id']:<6} {name:<25} {e['job_title'] or '—':<22} {dept:<18} {sal:>10}{status_tag}")
    separator()
    print(f"  Total: {len(employees)} record(s)\n")


def print_departments(depts):
    if not depts:
        print(Y + "  No departments found." + RST)
        return
    separator()
    print(W + f"{'ID':<6} {'Department Name':<30} {'Location':<25}" + RST)
    separator()
    for d in depts:
        print(f"{d['dept_id']:<6} {d['dept_name']:<30} {d['location'] or '—':<25}")
    separator()


def print_salary_report(rows):
    if not rows:
        print(Y + "  No data." + RST); return
    separator("═")
    print(W + f"{'Department':<22} {'HC':>4} {'Avg Salary':>12} {'Min':>12} {'Max':>12} {'Payroll':>14}" + RST)
    separator("═")
    for r in rows:
        print(
            f"{r['dept_name']:<22} {r['headcount']:>4} "
            f"${r['avg_salary']:>11,.2f} ${r['min_salary']:>11,.2f} "
            f"${r['max_salary']:>11,.2f} ${r['total_payroll']:>13,.2f}"
        )
    separator("═")


def print_audit(logs):
    if not logs:
        print(Y + "  No audit records." + RST); return
    separator()
    print(W + f"{'ID':<6} {'EmpID':<7} {'Employee':<22} {'Action':<8} {'When':<21} {'By'}" + RST)
    separator()
    for a in logs:
        emp_name = a.get("emp_name") or "—"
        print(f"{a['audit_id']:<6} {a['emp_id'] or '—':<7} {emp_name:<22} {a['action']:<8} {a['changed_at']:<21} {a['changed_by']}")
    separator()


def input_required(prompt):
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print(R + "  This field is required." + RST)


def input_float(prompt, required=True):
    while True:
        v = input(prompt).strip()
        if not v and not required:
            return None
        try:
            return float(v)
        except ValueError:
            print(R + "  Enter a valid number." + RST)


def input_int(prompt, required=True):
    while True:
        v = input(prompt).strip()
        if not v and not required:
            return None
        try:
            return int(v)
        except ValueError:
            print(R + "  Enter a valid integer." + RST)


def choose_department():
    depts = em.get_all_departments()
    print_departments(depts)
    return input_int("  Select Department ID: ")



def menu_add_employee():
    print(f"\n{W}── Add New Employee ─────────────────────────────────{RST}")
    first  = input_required("  First Name  : ")
    last   = input_required("  Last Name   : ")
    email  = input_required("  Email       : ")
    phone  = input("  Phone       : ").strip() or None
    job    = input_required("  Job Title   : ")
    salary = input_float("  Salary ($)  : ")
    dept_id = choose_department()
    em.add_employee(first, last, email, phone, job, salary, dept_id)


def menu_view_employees():
    print(f"\n{W}── View Employees ───────────────────────────────────{RST}")
    print("  1. Active employees")
    print("  2. Inactive employees")
    print("  3. By department")
    ch = input("  Choice: ").strip()
    if ch == "1":
        print_employees(em.get_all_employees("ACTIVE"))
    elif ch == "2":
        print_employees(em.get_all_employees("INACTIVE"))
    elif ch == "3":
        dept_id = choose_department()
        print_employees(em.get_employees_by_department(dept_id))
    else:
        print(R + "  Invalid choice." + RST)


def menu_search():
    kw = input_required("  Search keyword: ")
    results = em.search_employees(kw)
    print(f"\n  Found {len(results)} result(s):")
    print_employees(results)


def menu_update_employee():
    print(f"\n{W}── Update Employee ──────────────────────────────────{RST}")
    emp_id = input_int("  Employee ID: ")
    emp = em.get_employee_by_id(emp_id)
    if not emp:
        print(R + f"  Employee {emp_id} not found." + RST); return

    print(f"\n  Updating: {emp['first_name']} {emp['last_name']}  (leave blank to keep current)\n")
    updates = {}

    v = input(f"  First Name  [{emp['first_name']}]: ").strip()
    if v: updates["first_name"] = v

    v = input(f"  Last Name   [{emp['last_name']}]: ").strip()
    if v: updates["last_name"] = v

    v = input(f"  Email       [{emp['email']}]: ").strip()
    if v: updates["email"] = v

    v = input(f"  Phone       [{emp['phone'] or ''}]: ").strip()
    if v: updates["phone"] = v

    v = input(f"  Job Title   [{emp['job_title'] or ''}]: ").strip()
    if v: updates["job_title"] = v

    v = input(f"  Salary      [{emp['salary']}]: ").strip()
    if v:
        try: updates["salary"] = float(v)
        except ValueError: print(R + "  Invalid salary ignored." + RST)

    print("  Transfer department? (y/n): ", end="")
    if input().strip().lower() == "y":
        updates["dept_id"] = choose_department()

    if updates:
        em.update_employee(emp_id, **updates)
    else:
        print(Y + "  No changes made." + RST)


def menu_deactivate():
    emp_id = input_int("  Employee ID to deactivate: ")
    confirm = input(f"  Deactivate employee {emp_id}? (yes/no): ").strip().lower()
    if confirm == "yes":
        em.deactivate_employee(emp_id)
    else:
        print(Y + "  Cancelled." + RST)


def menu_departments():
    print(f"\n{W}── Department Menu ──────────────────────────────────{RST}")
    print("  1. List all departments")
    print("  2. Add department")
    ch = input("  Choice: ").strip()
    if ch == "1":
        print_departments(em.get_all_departments())
    elif ch == "2":
        name = input_required("  Dept Name : ")
        loc  = input("  Location  : ").strip() or None
        em.add_department(name, loc)
    else:
        print(R + "  Invalid choice." + RST)


def menu_reports():
    print(f"\n{W}── Reports ───────────────────────────────────────────{RST}")
    print("  1. Salary summary by department")
    print("  2. Audit log (last 20 actions)")
    ch = input("  Choice: ").strip()
    if ch == "1":
        print(f"\n{W}  ── Salary Report ──{RST}")
        print_salary_report(em.get_salary_report())
    elif ch == "2":
        print(f"\n{W}  ── Audit Log ──{RST}")
        print_audit(em.get_audit_log())
    else:
        print(R + "  Invalid choice." + RST)



MENU = [
    ("Add Employee",        menu_add_employee),
    ("View Employees",      menu_view_employees),
    ("Search Employees",    menu_search),
    ("Update Employee",     menu_update_employee),
    ("Deactivate Employee", menu_deactivate),
    ("Manage Departments",  menu_departments),
    ("Reports & Audit",     menu_reports),
    ("Exit",                None),
]


def main():
    banner()
    print(f"{G}  Initializing database …{RST}")
    initialize_database()
    print()

    while True:
        separator()
        print(f"{W}  MAIN MENU{RST}")
        separator()
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {C}{i}.{RST} {label}")
        separator()

        choice = input("  Select option: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU)):
            print(R + "  Invalid option. Try again." + RST)
            continue

        idx = int(choice) - 1
        label, handler = MENU[idx]

        if handler is None:          # Exit
            print(f"\n{G}  Goodbye! 👋{RST}\n")
            sys.exit(0)

        try:
            handler()
        except KeyboardInterrupt:
            print(Y + "\n  Cancelled." + RST)
        except Exception as exc:
            print(R + f"\n  ERROR: {exc}" + RST)

        input(f"\n{Y}  Press Enter to continue …{RST}")


if __name__ == "__main__":
    main()
