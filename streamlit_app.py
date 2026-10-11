"""Streamlit web front-end for the Hospital Management System.

It imports and reuses the helpers/constants from hospital_management.py
(CSV handling, ID generation, receipts, date parsing) so the same Python
code powers both the console program and this website.
"""
import csv
import statistics
from collections import Counter, defaultdict
from datetime import datetime

import streamlit as st

import hospital_management as hm

st.set_page_config(page_title="City Hospital Management", page_icon="🏥", layout="wide")
hm.ensure_files()


def show(header, rows):
    if rows:
        st.dataframe([dict(zip(header, r)) for r in rows], hide_index=True)
    else:
        st.info("No records.")


def append_row(filename, row):
    with open(filename, "a", newline="") as f:
        csv.writer(f).writerow(row)


def rewrite(filename, data):
    with open(filename, "w", newline="") as f:
        csv.writer(f).writerows(data)


# ---------------- login ----------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "cart" not in st.session_state:
    st.session_state.cart = []
if "receipt" not in st.session_state:
    st.session_state.receipt = None

if not st.session_state.auth:
    st.title("🏥 City Hospital Management")
    pw = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if pw.strip() == hm.PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid password.")
    st.caption("Demo password: 12345")
    st.stop()

st.title("🏥 City Hospital Management")
if st.button("Lock"):
    st.session_state.auth = False
    st.rerun()

t_pat, t_doc, t_med, t_rep = st.tabs(["Patients", "Doctors", "Pharmacy", "Reports"])

# ---------------- patients ----------------
with t_pat:
    st.subheader("Add patient")
    doctors = hm.read_rows(hm.DOCTOR_FILE)
    doc_options = [f"{d[0]} - {d[1]}" for d in doctors]
    with st.form("add_patient", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name")
        age = c2.number_input("Age", min_value=0, max_value=130, step=1)
        gender = c3.selectbox("Gender", ["Male", "Female", "Other"])
        phone = c1.text_input("Phone (10 digits)")
        disease = c2.text_input("Disease")
        inpatient = c3.selectbox("Inpatient?", ["No", "Yes"])
        bg = c1.text_input("Blood group")
        weight = c2.text_input("Weight (kg)")
        height = c3.text_input("Height (cm)")
        bp = c1.text_input("Blood pressure")
        temp = c2.text_input("Temperature")
        doctor = c3.selectbox("Doctor", doc_options)
        if st.form_submit_button("Add patient"):
            if not name.strip():
                st.error("Enter the name.")
            elif not (phone.isdigit() and len(phone) == 10):
                st.error("Enter a Valid Phone.No!!")
            elif not doctor:
                st.error("Add a doctor first.")
            else:
                pid = hm.next_id(hm.PATIENT_FILE, "P")
                date = datetime.now().strftime("%d-%m-%Y | %I:%M:%S %p")
                append_row(hm.PATIENT_FILE, [
                    pid, name.title(), int(age), gender, phone, disease.title(),
                    inpatient, date, bg.upper(), weight + "kg", height + "cm",
                    bp, temp, doctor.split(" - ")[0]])
                st.success(f"{name.title()} has been successfully added to the database!")

    st.subheader("Patients")
    q = st.text_input("Search patient by name", key="pq").strip().lower()
    show(hm.PATIENT_HEADER, [r for r in hm.read_rows(hm.PATIENT_FILE) if q in r[1].lower()])

# ---------------- doctors ----------------
with t_doc:
    st.subheader("Add doctor")
    with st.form("add_doctor", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dname = c1.text_input("Name")
        dgender = c2.selectbox("Gender", ["M", "F", "Other"])
        spec = c3.text_input("Speciality")
        hours = c1.text_input("Working hours")
        room = c2.text_input("Room")
        if st.form_submit_button("Add doctor"):
            if not hm.strip_dr(dname):
                st.error("Enter the name.")
            else:
                full = "Dr. " + hm.strip_dr(dname).title()
                append_row(hm.DOCTOR_FILE, [hm.next_id(hm.DOCTOR_FILE, "D"), full,
                                            dgender, spec.title(), hours, room.upper()])
                st.success(f"{full} has been successfully added")

    st.subheader("Doctors")
    dq = hm.strip_dr(st.text_input("Search doctor by name", key="dq")).lower()
    rows = hm.read_rows(hm.DOCTOR_FILE)
    show(hm.DOCTOR_HEADER, [r for r in rows if dq in r[1].lower()])

    if rows:
        st.subheader("Delete doctor")
        target = st.selectbox("Choose a doctor", [f"{r[0]} - {r[1]}" for r in rows])
        if st.button("Delete doctor"):
            with open(hm.DOCTOR_FILE, newline="") as f:
                data = [r for r in csv.reader(f)]
            data = [r for i, r in enumerate(data) if i == 0 or r[0] != target.split(" - ")[0]]
            rewrite(hm.DOCTOR_FILE, data)
            st.success(f"{target.split(' - ')[1]} has been successfully deleted from the database.")

# ---------------- pharmacy ----------------
with t_med:
    st.subheader("Add medicine")
    with st.form("add_med", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        mname = c1.text_input("Name").strip().title()
        price = c2.number_input("Price of 1 unit", min_value=0, step=1)
        use = c3.text_input("Use")
        stock = c1.number_input("Stock", min_value=0, step=1)
        company = c2.text_input("Company")
        expiry = c3.date_input("Expiry date")
        if st.form_submit_button("Add medicine"):
            existing = {r[1].lower() for r in hm.read_rows(hm.MEDICINE_FILE)}  # set
            if not mname:
                st.error("Enter the name.")
            elif mname.lower() in existing:
                st.error(f"{mname} already exists. Use 'Change stock' below.")
            else:
                append_row(hm.MEDICINE_FILE, [hm.next_id(hm.MEDICINE_FILE, "M"), mname,
                                              use.title(), int(stock), int(price),
                                              expiry.isoformat(), company.title()])
                st.success(f"The medicine {mname} has been successfully added")

    meds = hm.read_rows(hm.MEDICINE_FILE)
    st.subheader("Available medicines")
    mq = st.text_input("Search medicine by name", key="mq").strip().lower()
    show(hm.MEDICINE_HEADER, [r for r in meds if mq in r[1].lower()])

    if meds:
        st.subheader("Change stock")
        c1, c2 = st.columns(2)
        pick = c1.selectbox("Medicine", [r[1] for r in meds], key="stock_pick")
        new_stock = c2.number_input("Updated stock", min_value=0, step=1, key="stock_new")
        if st.button("Update stock"):
            with open(hm.MEDICINE_FILE, newline="") as f:
                data = list(csv.reader(f))
            for r in data[1:]:
                if r and r[1] == pick:
                    r[3] = str(int(new_stock))
            rewrite(hm.MEDICINE_FILE, data)
            st.success(f"The stock of {pick} has been successfully changed to {int(new_stock)}")

        st.subheader("Sell medicine")
        c1, c2 = st.columns(2)
        sell_med = c1.selectbox("Medicine", [r[1] for r in meds], key="sell_pick")
        sell_qty = c2.number_input("Units", min_value=1, step=1, key="sell_qty")
        if st.button("Add to bill"):
            row = next(r for r in meds if r[1] == sell_med)
            in_cart = sum(q for n, q in st.session_state.cart if n == sell_med)
            if sell_qty + in_cart > hm.to_int(row[3]):
                st.error(f"Only {row[3]} units of {sell_med} are available.")
            else:
                st.session_state.cart.append((sell_med, int(sell_qty)))
                st.session_state.receipt = None

        if st.session_state.cart:
            show(["Medicine", "Units"], [list(c) for c in st.session_state.cart])
            b1, b2 = st.columns(2)
            if b2.button("Clear bill"):
                st.session_state.cart = []
                st.rerun()
            if b1.button("Complete sale"):
                with open(hm.MEDICINE_FILE, newline="") as f:
                    data = list(csv.reader(f))
                items, total = [], 0
                for n, q in st.session_state.cart:
                    row = next((r for r in data[1:] if r and r[1] == n), None)
                    if row is None or q > hm.to_int(row[3]):
                        st.warning(f"Skipped {n}: not enough stock.")
                        continue
                    row[3] = str(hm.to_int(row[3]) - q)
                    sub = float(row[4]) * q
                    total += sub
                    items.append([row[0], row[1], q, row[4], f"{sub:.2f}"])
                if items:
                    rewrite(hm.MEDICINE_FILE, data)
                    rec = hm.next_receipt()
                    date = datetime.now().strftime("%d-%m-%Y")
                    for it in items:
                        append_row(hm.SALES_FILE, [rec, date, it[0], it[1], it[2], it[4]])
                    st.session_state.receipt = (rec, date, items, total)
                st.session_state.cart = []
                st.rerun()

    if st.session_state.receipt:
        rec, date, items, total = st.session_state.receipt
        st.markdown(f"**CITY HOSPITAL - PHARMACY** \nReceipt No.: {rec} \nDate: {date}")
        show(["Medicine ID", "Name", "Quantity", "Price Per Unit", "Subtotal"], items)
        st.markdown(f"**Total: ₹{total:.2f}**  \nThank you for your purchase. Have a nice day!")

# ---------------- reports ----------------
with t_rep:
    meds = hm.load_records(hm.MEDICINE_FILE, hm.MEDICINE_HEADER)   # dict
    patients = hm.read_rows(hm.PATIENT_FILE)

    st.subheader("Low stock medicines")
    limit = st.number_input("Stock at or below", min_value=0, value=10, step=1)
    low = sorted(((m["Medicine ID"], m["Name"], hm.to_int(m["Stock"]))
                  for m in meds.values() if hm.to_int(m["Stock"]) <= limit),
                 key=lambda t: t[2])
    show(["Medicine ID", "Name", "Stock"], [list(t) for t in low])

    st.subheader("Expired / expiring medicines")
    days = st.number_input("Within how many days", min_value=0, value=30, step=1)
    today = datetime.now().date()
    soon, unreadable = [], []
    for m in meds.values():
        exp = hm.parse_date(m["Expiry Date"])
        if exp is None:
            unreadable.append(m["Name"])
            continue
        left = (exp - today).days
        if left <= days:
            soon.append((left, [m["Medicine ID"], m["Name"], m["Expiry Date"],
                                "EXPIRED" if left < 0 else f"{left} day(s) left"]))
    show(["Medicine ID", "Name", "Expiry Date", "Status"], [r for _, r in sorted(soon)])
    if unreadable:
        st.caption("Could not read expiry date for: " + ", ".join(unreadable))

    st.subheader("Patients per doctor")
    doctors_d = hm.load_records(hm.DOCTOR_FILE, hm.DOCTOR_HEADER)  # dict
    counts = Counter(r[13] for r in patients)
    per = [[i, d["Name"], d["Speciality"], counts.get(i, 0)] for i, d in doctors_d.items()]
    per += [[i, "Unknown / removed", "-", c] for i, c in counts.items() if i not in doctors_d]
    show(["Doctor ID", "Doctor", "Speciality", "Patients"], sorted(per, key=lambda r: -r[3]))

    st.subheader("Patient statistics")
    if patients:
        ages = [hm.to_int(r[2]) for r in patients]
        inp = Counter(r[6].title() for r in patients)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total patients", len(patients))
        m2.metric("Average age", f"{statistics.mean(ages):.1f}")
        m3.metric("Median age", statistics.median(ages))
        m4.metric("Min / Max age", f"{min(ages)} / {max(ages)}")
        m5.metric("Inpatients", inp.get("Yes", 0))
        c1, c2 = st.columns(2)
        diseases = Counter(r[5].title() for r in patients).most_common(5)
        c1.caption("Most common diseases")
        c1.bar_chart({d: c for d, c in diseases})
        c2.caption("Gender distribution")
        c2.bar_chart(dict(Counter(r[3].title() for r in patients)))
        st.caption("Blood groups")
        show(["Blood Group", "Count"], [list(t) for t in Counter(r[8].upper() for r in patients).most_common()])
    else:
        st.info("No patient records to analyse.")

    st.subheader("Pharmacy sales summary")
    sales = hm.read_rows(hm.SALES_FILE)
    if sales:
        units, revenue = defaultdict(int), defaultdict(float)
        for r in sales:
            units[r[3]] += hm.to_int(r[4])
            revenue[r[3]] += float(r[5])
        s1, s2, s3 = st.columns(3)
        s1.metric("Receipts issued", len({r[0] for r in sales}))
        s2.metric("Total revenue", f"₹{sum(revenue.values()):.2f}")
        best = max(units, key=units.get)
        s3.metric("Best seller", best)
        show(["Medicine", "Units Sold", "Revenue (₹)"],
             [[n, units[n], f"{revenue[n]:.2f}"] for n in sorted(units, key=units.get, reverse=True)])
    else:
        st.info("No sales have been recorded yet.")
