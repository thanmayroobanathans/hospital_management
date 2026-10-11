from prettytable import PrettyTable
from datetime import datetime
import csv
import os
import re
import statistics
from collections import Counter, defaultdict

PASSWORD = '12345'  # fine for a school project; use hashing/env vars for real use

PATIENT_FILE = 'patients.csv'
DOCTOR_FILE = 'doctor.csv'
MEDICINE_FILE = 'medicine.csv'
RECEIPT_FILE = 'receipt_no.txt'
SALES_FILE = 'sales.csv'

PATIENT_HEADER = ["Patient ID", "Name", "Age", "Gender", "Phone",
                  "Disease", "In Patient", "Date & Time", "Blood Group",
                  "Weight", "Height", "BP", "Temperature", "Doctor ID"]
DOCTOR_HEADER = ['Doctor ID', 'Name', 'Gender', 'Speciality', 'Working Hours', 'Room']
MEDICINE_HEADER = ['Medicine ID', 'Name', 'Use', 'Stock', 'Cost Per Unit',
                   'Expiry Date', 'Company name']
SALES_HEADER = ['Receipt No', 'Date', 'Medicine ID', 'Name', 'Quantity', 'Subtotal']


# ---------- helpers ----------
def ensure_files():
    """Create any missing CSV with its header row (fixes empty-file crashes)."""
    for fname, header in ((PATIENT_FILE, PATIENT_HEADER),
                          (DOCTOR_FILE, DOCTOR_HEADER),
                          (MEDICINE_FILE, MEDICINE_HEADER),
                          (SALES_FILE, SALES_HEADER)):
        if not os.path.exists(fname):
            with open(fname, 'w', newline='') as f:
                csv.writer(f).writerow(header)


def read_rows(filename):
    """Return data rows only (header skipped)."""
    with open(filename, 'r', newline='') as f:
        r = csv.reader(f)
        next(r, None)
        return [row for row in r if row]


def next_id(filename, prefix):
    """Next ID like P001; works when the file only has a header."""
    rows = read_rows(filename)
    if not rows:
        return prefix + '001'
    try:
        return prefix + str(int(rows[-1][0][1:]) + 1).zfill(3)
    except ValueError:
        return prefix + str(len(rows) + 1).zfill(3)


def strip_dr(name):
    """Remove a leading 'Dr' / 'Dr.' so names compare consistently."""
    return re.sub(r'^dr\.?\s+|^dr\.', '', name.strip(), flags=re.I).strip()


def to_int(value, default=0):
    """Safe int conversion for values read from CSV."""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def load_records(filename, header):
    """Load a CSV into a dictionary: {ID: {column name: value}} for fast lookup."""
    return {row[0]: dict(zip(header, row)) for row in read_rows(filename)}


def parse_date(text):
    """Try common date formats; return a date or None if unreadable."""
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def get_int(prompt, minimum=None):
    """Keep asking until a valid integer is entered."""
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print('Please enter a valid number.')
            continue
        if minimum is not None and value < minimum:
            print(f'Value must be at least {minimum}.')
            continue
        return value


def show_table(header, rows):
    table = PrettyTable()
    table.field_names = header
    table.add_rows(rows)
    print(table)


def next_receipt():
    """Persistent receipt number so it doesn't reset to R001 on restart."""
    n = 1
    if os.path.exists(RECEIPT_FILE):
        try:
            with open(RECEIPT_FILE) as f:
                n = int(f.read().strip())
        except ValueError:
            n = 1
    with open(RECEIPT_FILE, 'w') as f:
        f.write(str(n + 1))
    return 'R' + str(n).zfill(3)


# ---------- patients ----------
def addpatient():
    name = input('enter the name :').title()
    age = get_int('enter the age :', 0)
    gender = input('enter the gender :').title()
    while True:
        phone_no = input('enter the phone.no of the patient :')
        if phone_no.isdigit() and len(phone_no) == 10:
            break
        print('Enter a Valid Phone.No!!')
    disease = input('enter the disease which the person is suffering from :').title()
    in_patient = input('Enter (Yes/No) if he/she is an inpatient :').title()
    date = datetime.now().strftime("%d-%m-%Y | %I:%M:%S %p")
    bloodgroup = input('Enter the Blood Group of the patient :').upper()
    weight = input('Enter the weight of the patient :') + 'kg'
    height = input('Enter the height of the patient :') + 'cm'
    blood_pressure = input('Enter the blood pressure of the patient:')
    temperature = input('Enter the temperature of the patient :')
    displaydoctors()
    doctorid = input('Enter the doctor id for the patient :').upper()
    patientid = next_id(PATIENT_FILE, 'P')
    patient = [patientid, name, age, gender, phone_no, disease, in_patient, date,
               bloodgroup, weight, height, blood_pressure, temperature, doctorid]
    with open(PATIENT_FILE, 'a', newline='') as f:
        csv.writer(f).writerow(patient)
    print()
    displaypatients()
    print()
    print(f'{name} has been successfully added to the database!')
    print('=============================')
    print()


def displaypatients():
    show_table(PATIENT_HEADER, read_rows(PATIENT_FILE))


def searchpatient():
    n = input('enter the patient to be searched :').strip().lower()
    data = [row for row in read_rows(PATIENT_FILE) if n in row[1].lower()]
    show_table(PATIENT_HEADER, data)


# ---------- doctors ----------
def adddoctor():
    # Always store as "Dr. Name" (single prefix, one consistent format)
    name = 'Dr. ' + strip_dr(input('enter the name :')).title()
    gender = input('enter the gender of the doctor :').upper()
    speciality = input('enter the speciality :').title()
    doctorid = next_id(DOCTOR_FILE, 'D')
    workinghours = input('enter the working hours :')
    room = input('enter the room/consultation room :').upper()
    with open(DOCTOR_FILE, 'a', newline='') as f:
        csv.writer(f).writerow([doctorid, name, gender, speciality, workinghours, room])
    displaydoctors()
    print(f'{name} has been successfully added')
    print(40 * '=')


def displaydoctors():
    show_table(DOCTOR_HEADER, read_rows(DOCTOR_FILE))


def deletedoctor():
    displaydoctors()
    n = strip_dr(input('Enter the name of the doctor: ')).lower()

    with open(DOCTOR_FILE, 'r', newline='') as f:
        data = list(csv.reader(f))

    deleted = None
    for i in range(1, len(data)):
        if n and n in data[i][1].lower():
            deleted = data.pop(i)[1]
            break

    if deleted:
        with open(DOCTOR_FILE, 'w', newline='') as f:
            csv.writer(f).writerows(data)
        print(f'{deleted} has been successfully deleted from the database.')
    else:
        print(f'Dr. {n.title()} is not present in the database.')


def searchdoctor():
    n = strip_dr(input('enter the doctor to be searched :')).lower()
    data = [row for row in read_rows(DOCTOR_FILE) if n in row[1].lower()]
    show_table(DOCTOR_HEADER, data)


# ---------- medicines ----------
def addmedicine():
    medicineid = next_id(MEDICINE_FILE, 'M')
    name = input('enter the name of the medicine :').strip().title()
    existing_names = {row[1].lower() for row in read_rows(MEDICINE_FILE)}  # set
    if name.lower() in existing_names:
        print(f'{name} already exists. Use "change the stock" to update it.')
        return
    cost_unit = get_int('enter the price of 1 unit :', 0)
    use = input('Enter the use of the given medicine :').title()
    quantity = get_int('enter the stock :', 0)
    company = input('Enter the company where the following medicine has been purchased :').title()
    exp = input('enter the expiry date :')
    row = [medicineid, name, use, quantity, cost_unit, exp, company]
    with open(MEDICINE_FILE, 'a', newline='') as f:
        csv.writer(f).writerow(row)
    displaymedicines()
    print()
    print(f'The medicine {name} has been successfully added')
    print('=' * 40)


def displaymedicines():
    show_table(MEDICINE_HEADER, read_rows(MEDICINE_FILE))


def searchmedicine():
    n = input('enter the name of the medicine : ').strip().lower()
    data = [row for row in read_rows(MEDICINE_FILE) if n in row[1].lower()]
    show_table(MEDICINE_HEADER, data)


def changestock():
    displaymedicines()
    medicine = input('Enter the medicine to be changed: ').strip().lower()
    n = get_int('Enter the updated stock: ', 0)
    with open(MEDICINE_FILE, 'r', newline='') as f:
        data = list(csv.reader(f))
    changed = False
    for row in data[1:]:
        if row and row[1].lower() == medicine:
            row[3] = str(n)
            changed = True
    if not changed:
        print(f'{medicine.title()} was not found in the medicine database.')
        return
    with open(MEDICINE_FILE, 'w', newline='') as f:
        csv.writer(f).writerows(data)
    print(f'The stock of {medicine.title()} has been successfully changed to {n}')


def sellmedicine():
    n = get_int('Enter the no of medicines to be sold: ', 1)
    displaymedicines()
    print()

    with open(MEDICINE_FILE, 'r', newline='') as f:
        data = list(csv.reader(f))

    total = 0
    med = []
    for _ in range(n):
        a = input('Enter the medicine: ').strip().lower()
        b = get_int('Enter the no of units to be sold: ', 1)
        match = next((row for row in data[1:] if row and row[1].lower() == a), None)
        if match is None:
            print(f'{a.title()} was not found in the medicine database.')
            continue
        stock = int(match[3])
        if b > stock:
            print(f'Only {stock} units of {match[1]} are available.')
            continue
        match[3] = str(stock - b)
        subtotal = float(match[4]) * b
        total += subtotal
        med.append([match[0], match[1], b, match[4], f'{subtotal:.2f}'])
        print(f'{b} units of {match[1]} sold successfully.')

    if not med:
        print('No medicines were sold, so no receipt was generated.')
        return

    # write stock back once, after all items are processed
    with open(MEDICINE_FILE, 'w', newline='') as f:
        csv.writer(f).writerows(data)

    rec = next_receipt()
    sale_date = datetime.now().strftime("%d-%m-%Y")
    with open(SALES_FILE, 'a', newline='') as f:  # log every sale for reports
        w = csv.writer(f)
        for item in med:
            w.writerow([rec, sale_date, item[0], item[1], item[2], item[4]])
    print('=' * 64)
    print('CITY HOSPITAL'.center(64))
    print('PHARMACY'.center(64))
    print('=' * 64)
    print(f'Receipt No.: {rec}')
    print(f'Date       : {datetime.now().strftime("%d-%m-%Y")}')
    print('-' * 64)
    show_table(['Medicine ID', 'Name', 'Quantity', 'Price Per Unit', 'Subtotal'], med)
    print('-' * 64)
    print(f'Total : ₹{total:.2f}')
    print('=' * 64)
    print('Thank you for your purchase'.center(64))
    print('Have a nice day!!!'.center(64))
    print('=' * 64)
    print()


# ---------- reports & analysis ----------
def lowstock_report():
    threshold = get_int('Show medicines with stock at or below: ', 0)
    meds = load_records(MEDICINE_FILE, MEDICINE_HEADER)
    low = [(m['Medicine ID'], m['Name'], to_int(m['Stock']))
           for m in meds.values() if to_int(m['Stock']) <= threshold]
    low.sort(key=lambda t: t[2])
    print(f'\nMedicines with stock <= {threshold}:')
    if low:
        show_table(['Medicine ID', 'Name', 'Stock'], low)
    else:
        print('No medicines are running low.')


def expiry_report():
    days = get_int('Show medicines expiring within how many days: ', 0)
    today = datetime.now().date()
    meds = load_records(MEDICINE_FILE, MEDICINE_HEADER)
    soon, unreadable = [], []
    for m in meds.values():
        exp = parse_date(m['Expiry Date'])
        if exp is None:
            unreadable.append(m['Name'])
            continue
        left = (exp - today).days
        if left <= days:
            status = 'EXPIRED' if left < 0 else f'{left} day(s) left'
            soon.append((left, [m['Medicine ID'], m['Name'], m['Expiry Date'], status]))
    soon.sort(key=lambda t: t[0])
    print(f'\nMedicines expired or expiring within {days} days:')
    if soon:
        show_table(['Medicine ID', 'Name', 'Expiry Date', 'Status'], [r for _, r in soon])
    else:
        print('Nothing is expiring in that period.')
    if unreadable:
        print('Could not read expiry date for:', ', '.join(unreadable))


def patients_per_doctor():
    patients = read_rows(PATIENT_FILE)
    doctors = load_records(DOCTOR_FILE, DOCTOR_HEADER)
    counts = Counter(row[13] for row in patients)  # doctor id -> number of patients
    rows = []
    for doc_id, d in doctors.items():
        rows.append([doc_id, d['Name'], d['Speciality'], counts.get(doc_id, 0)])
    for doc_id, c in counts.items():  # patients whose doctor was deleted / mistyped
        if doc_id not in doctors:
            rows.append([doc_id, 'Unknown / removed', '-', c])
    rows.sort(key=lambda r: r[3], reverse=True)
    print('\nPatients per doctor:')
    show_table(['Doctor ID', 'Doctor', 'Speciality', 'Patients'], rows)


def patient_statistics():
    patients = read_rows(PATIENT_FILE)
    if not patients:
        print('No patient records to analyse.')
        return
    ages = [to_int(r[2]) for r in patients]
    print('\nPatient statistics')
    print('-' * 40)
    print(f'Total patients : {len(patients)}')
    print(f'Age (min/avg/median/max): {min(ages)} / {statistics.mean(ages):.1f} / '
          f'{statistics.median(ages)} / {max(ages)}')
    inpatients = Counter(r[6].title() for r in patients)
    print(f'Inpatients     : {inpatients.get("Yes", 0)}   Outpatients: {inpatients.get("No", 0)}')
    print('\nGender distribution:')
    show_table(['Gender', 'Count'], Counter(r[3].title() for r in patients).most_common())
    print('\nMost common diseases:')
    show_table(['Disease', 'Cases'], Counter(r[5].title() for r in patients).most_common(5))
    print('\nBlood group distribution:')
    show_table(['Blood Group', 'Count'], Counter(r[8].upper() for r in patients).most_common())


def sales_summary():
    sales = read_rows(SALES_FILE)
    if not sales:
        print('No sales have been recorded yet.')
        return
    units = defaultdict(int)
    revenue = defaultdict(float)
    for receipt, date, mid, name, qty, subtotal in (r[:6] for r in sales):
        units[name] += to_int(qty)
        revenue[name] += float(subtotal)
    total = sum(revenue.values())
    receipts = len({r[0] for r in sales})  # set -> unique receipts
    print('\nSales summary')
    print('-' * 40)
    print(f'Receipts issued : {receipts}')
    print(f'Total revenue   : ₹{total:.2f}')
    rows = sorted(((n, units[n], f'{revenue[n]:.2f}') for n in units),
                  key=lambda t: t[1], reverse=True)
    show_table(['Medicine', 'Units Sold', 'Revenue (₹)'], rows)
    print(f'Best seller: {rows[0][0]} ({rows[0][1]} units)')


# ---------- menus ----------
def back_to_main():
    print()
    print('---------------------------------------------------------------------------')
    print('---WELCOME BACK TO THE MAIN MENU---'.center(70))


def patientmenu():
    print('---------------------------------')
    print('Welcome to the patient management')
    print()
    while True:
        print('1.add patient to the database\n')
        print('2.search patient by name\n')
        print('3.display patient details\n')
        print('4.exit\n')
        a = get_int('enter your choice: ')
        if a == 1:
            addpatient()
        elif a == 2:
            searchpatient()
        elif a == 3:
            displaypatients()
        elif a == 4:
            back_to_main()
            break
        else:
            print('invalid option')


def doctormenu():
    print('-------------------------------')
    print('Welcome to the doctor management')
    while True:
        print('1.add doctor\n')
        print('2.search doctor\n')
        print('3.display doctors\n')
        print('4.delete doctor\n')
        print('5.exit\n')
        a = get_int('enter your choice: ')
        if a == 1:
            adddoctor()
        elif a == 2:
            searchdoctor()
        elif a == 3:
            displaydoctors()
        elif a == 4:
            deletedoctor()
        elif a == 5:
            back_to_main()
            break
        else:
            print('invalid option')


def medicinemenu():
    print('---------------------------------------')
    print('Welcome to the Pharmacy management')
    print()
    while True:
        print('1.add medicine to available stock\n')
        print('2.search medicine by name\n')
        print('3.display available medicine\n')
        print('4.change the stock of a medicine\n')
        print('5.sell medicine(profit)\n')
        print('6.exit\n')
        a = get_int('enter your choice: ')
        if a == 1:
            addmedicine()
        elif a == 2:
            searchmedicine()
        elif a == 3:
            displaymedicines()
        elif a == 4:
            changestock()
        elif a == 5:
            sellmedicine()
        elif a == 6:
            back_to_main()
            break
        else:
            print('invalid option')


def reportsmenu():
    print('---------------------------------------')
    print('Welcome to Reports & Analysis')
    print()
    while True:
        print('1.low stock medicines\n')
        print('2.expired / expiring medicines\n')
        print('3.patients per doctor\n')
        print('4.patient statistics\n')
        print('5.pharmacy sales summary\n')
        print('6.exit\n')
        a = get_int('enter your choice: ')
        if a == 1:
            lowstock_report()
        elif a == 2:
            expiry_report()
        elif a == 3:
            patients_per_doctor()
        elif a == 4:
            patient_statistics()
        elif a == 5:
            sales_summary()
        elif a == 6:
            back_to_main()
            break
        else:
            print('invalid option')


def authorization():
    password = input('Enter the password :').strip()
    if password == PASSWORD:
        print('Access Granted.')
        return True
    print('Invalid password.')
    return False


# ---------- main ----------
def main():
    ensure_files()
    print('===WELCOME TO HOSPITAL MANAGEMENT====')
    while True:
        print('1.patient management'.title())
        print()
        print('2.doctor management'.title())
        print()
        print('3.Pharmacy management'.title())
        print()
        print('4.Reports & Analysis')
        print()
        print('5.Exit')
        print()
        ch = input('enter your choice: ').strip()
        if ch == '1':
            if authorization():
                patientmenu()
        elif ch == '2':
            if authorization():
                doctormenu()
        elif ch == '3':
            if authorization():
                medicinemenu()
        elif ch == '4':
            if authorization():
                reportsmenu()
        elif ch == '5':
            print('Hope you have a nice day!!')
            break
        else:
            print('Invalid option,Choose again')


if __name__ == '__main__':
    main()
