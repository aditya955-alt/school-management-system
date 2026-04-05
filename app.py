import json
import os
import sqlite3
from io import BytesIO
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'school.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
    return db


def init_db():
    if not os.path.exists(DATABASE_PATH):
        with app.app_context():
            db = get_db()
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                db.executescript(f.read())
            db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.', 'error')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = query_db('SELECT * FROM login WHERE username = ? AND password = ?', (username, password), one=True)
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    total_students = query_db('SELECT COUNT(*) AS total FROM student', one=True)['total']
    total_staff = query_db('SELECT COUNT(*) AS total FROM staff', one=True)['total']
    total_classes = query_db('SELECT COUNT(DISTINCT class_name) AS total FROM student', one=True)['total']
    pending_fees = query_db("SELECT COUNT(*) AS total FROM student_fee WHERE status = 'Pending'", one=True)['total']

    students_per_class = query_db('SELECT class_name AS label, COUNT(*) AS value FROM student GROUP BY class_name')
    fees_by_status = query_db('SELECT status AS label, COUNT(*) AS value FROM student_fee GROUP BY status')
    class_data = [{'label': row['label'], 'value': row['value']} for row in students_per_class]
    fee_data = [{'label': row['label'], 'value': row['value']} for row in fees_by_status]

    return render_template(
        'dashboard.html',
        role=session['role'],
        totals={
            'students': total_students,
            'staff': total_staff,
            'classes': total_classes,
            'pending_fees': pending_fees
        },
        students_per_class=json.dumps(class_data),
        fees_by_status=json.dumps(fee_data)
    )


@app.route('/students', methods=['GET', 'POST'])
@login_required()
def students():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db(
                'INSERT INTO student (name, roll_number, class_name, section, email) VALUES (?, ?, ?, ?, ?)',
                (request.form['name'], request.form['roll_number'], request.form['class_name'], request.form['section'], request.form['email'])
            )
            flash('Student added successfully.', 'success')
        elif action == 'edit':
            execute_db(
                'UPDATE student SET name = ?, roll_number = ?, class_name = ?, section = ?, email = ? WHERE id = ?',
                (request.form['name'], request.form['roll_number'], request.form['class_name'], request.form['section'], request.form['email'], request.form['id'])
            )
            flash('Student updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM student WHERE id = ?', (request.form['id'],))
            flash('Student deleted successfully.', 'success')
        return redirect(url_for('students'))

    search = request.args.get('search', '').strip()
    if search:
        like_pattern = f'%{search}%'
        students = query_db(
            'SELECT * FROM student WHERE name LIKE ? OR roll_number LIKE ? OR class_name LIKE ? OR email LIKE ? ORDER BY name',
            (like_pattern, like_pattern, like_pattern, like_pattern)
        )
    else:
        students = query_db('SELECT * FROM student ORDER BY name')

    return render_template('students.html', students=students, role=role, search=search)


@app.route('/staff', methods=['GET', 'POST'])
@login_required()
def staff():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db(
                'INSERT INTO staff (name, classes_taught, subjects_taught, email) VALUES (?, ?, ?, ?)',
                (request.form['name'], request.form['classes_taught'], request.form['subjects_taught'], request.form['email'])
            )
            flash('Staff added successfully.', 'success')
        elif action == 'edit':
            execute_db(
                'UPDATE staff SET name = ?, classes_taught = ?, subjects_taught = ?, email = ? WHERE id = ?',
                (request.form['name'], request.form['classes_taught'], request.form['subjects_taught'], request.form['email'], request.form['id'])
            )
            flash('Staff updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM staff WHERE id = ?', (request.form['id'],))
            flash('Staff deleted successfully.', 'success')
        return redirect(url_for('staff'))

    search = request.args.get('search', '').strip()
    if search:
        like_pattern = f'%{search}%'
        staff_members = query_db(
            'SELECT * FROM staff WHERE name LIKE ? OR classes_taught LIKE ? OR subjects_taught LIKE ? OR email LIKE ? ORDER BY name',
            (like_pattern, like_pattern, like_pattern, like_pattern)
        )
    else:
        staff_members = query_db('SELECT * FROM staff ORDER BY name')

    return render_template('staff.html', staff=staff_members, role=role, search=search)


@app.route('/sections', methods=['GET', 'POST'])
@login_required()
def sections():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db('INSERT INTO section_subject_teacher (section, subject, teacher_id) VALUES (?, ?, ?)',
                       (request.form['section'], request.form['subject'], request.form['teacher_id']))
            flash('Assignment added successfully.', 'success')
        elif action == 'edit':
            execute_db('UPDATE section_subject_teacher SET section = ?, subject = ?, teacher_id = ? WHERE id = ?',
                       (request.form['section'], request.form['subject'], request.form['teacher_id'], request.form['id']))
            flash('Assignment updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM section_subject_teacher WHERE id = ?', (request.form['id'],))
            flash('Assignment deleted successfully.', 'success')
        return redirect(url_for('sections'))

    assignments = query_db('SELECT sst.*, staff.name as teacher_name FROM section_subject_teacher sst JOIN staff ON sst.teacher_id = staff.id')
    teachers = query_db('SELECT * FROM staff ORDER BY name')
    return render_template('sections.html', assignments=assignments, teachers=teachers, role=role)


@app.route('/fees', methods=['GET', 'POST'])
@login_required()
def fees():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db('INSERT INTO student_fee (student_id, amount, payment_date, status) VALUES (?, ?, ?, ?)',
                       (request.form['student_id'], request.form['amount'], request.form['payment_date'], request.form['status']))
            flash('Fee record added successfully. You can download the receipt below.', 'success')
        elif action == 'edit':
            execute_db('UPDATE student_fee SET student_id = ?, amount = ?, payment_date = ?, status = ? WHERE id = ?',
                       (request.form['student_id'], request.form['amount'], request.form['payment_date'], request.form['status'], request.form['id']))
            flash('Fee record updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM student_fee WHERE id = ?', (request.form['id'],))
            flash('Fee record deleted successfully.', 'success')
        return redirect(url_for('fees'))

    if role == 'student':
        login_user = query_db('SELECT * FROM login WHERE id = ?', (session['user_id'],), one=True)
        if login_user and login_user['user_id']:
            records = query_db(
                'SELECT sf.*, student.name as student_name, student.roll_number FROM student_fee sf JOIN student ON sf.student_id = student.id WHERE student.id = ? ORDER BY sf.payment_date DESC',
                (login_user['user_id'],)
            )
        else:
            records = []
        students = []
    else:
        records = query_db('SELECT sf.*, student.name as student_name, student.roll_number FROM student_fee sf JOIN student ON sf.student_id = student.id ORDER BY sf.payment_date DESC')
        students = query_db('SELECT * FROM student ORDER BY name')
    return render_template('fees.html', records=records, students=students, role=role)


@app.route('/salaries', methods=['GET', 'POST'])
@login_required(role='admin')
def salaries():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            execute_db('INSERT INTO teacher_salary (staff_id, amount, payment_date, status) VALUES (?, ?, ?, ?)',
                       (request.form['staff_id'], request.form['amount'], request.form['payment_date'], request.form['status']))
            flash('Salary record added successfully.', 'success')
        elif action == 'edit':
            execute_db('UPDATE teacher_salary SET staff_id = ?, amount = ?, payment_date = ?, status = ? WHERE id = ?',
                       (request.form['staff_id'], request.form['amount'], request.form['payment_date'], request.form['status'], request.form['id']))
            flash('Salary record updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM teacher_salary WHERE id = ?', (request.form['id'],))
            flash('Salary record deleted successfully.', 'success')
        return redirect(url_for('salaries'))

    salaries = query_db('SELECT ts.*, staff.name as teacher_name FROM teacher_salary ts JOIN staff ON ts.staff_id = staff.id ORDER BY ts.payment_date DESC')
    teachers = query_db('SELECT * FROM staff ORDER BY name')
    return render_template('salaries.html', salaries=salaries, teachers=teachers)


@app.route('/fee-receipt/<int:fee_id>')
@login_required()
def fee_receipt(fee_id):
    record = query_db(
        'SELECT sf.*, student.name AS student_name, student.roll_number FROM student_fee sf JOIN student ON sf.student_id = student.id WHERE sf.id = ?',
        (fee_id,),
        one=True
    )
    if not record:
        abort(404)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle('Fee Receipt')
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawString(50, 740, 'College Management System')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(50, 725, 'School Name: Greenfield College')
    pdf.drawString(50, 710, 'Address: 123 Campus Drive, City')
    pdf.drawString(50, 695, 'Phone: (555) 123-4567')

    pdf.setStrokeColorRGB(0.2, 0.4, 0.8)
    pdf.setLineWidth(2)
    pdf.line(50, 685, 550, 685)

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(50, 660, 'Fee Receipt')

    pdf.setFont('Helvetica', 12)
    pdf.drawString(50, 630, f'Student Name: {record["student_name"]}')
    pdf.drawString(50, 610, f'Roll Number: {record["roll_number"]}')
    pdf.drawString(50, 590, f'Amount Paid: ₹{record["amount"]:.2f}')
    pdf.drawString(50, 570, f'Payment Date: {record["payment_date"]}')
    pdf.drawString(50, 550, f'Status: {record["status"]}')

    pdf.rect(420, 620, 120, 80, stroke=1, fill=0)
    pdf.setFont('Helvetica', 10)
    pdf.drawString(430, 660, 'SCHOOL LOGO')
    pdf.drawString(430, 645, '(Placeholder)')

    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(50, 520, 'Thank you for your payment. Keep this receipt for your records.')
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'fee_receipt_{record["roll_number"]}.pdf',
        mimetype='application/pdf'
    )


@app.route('/attendance', methods=['GET', 'POST'])
@login_required()
def attendance():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db(
                'INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                (request.form['student_id'], request.form['date'], request.form['status'])
            )
            flash('Attendance marked successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM attendance WHERE id = ?', (request.form['id'],))
            flash('Attendance record deleted successfully.', 'success')
        return redirect(url_for('attendance'))

    if role == 'student':
        login_user = query_db('SELECT * FROM login WHERE id = ?', (session['user_id'],), one=True)
        if not login_user or not login_user['user_id']:
            flash('Student profile not found.', 'error')
            return redirect(url_for('dashboard'))
        records = query_db(
            'SELECT a.*, student.name, student.roll_number FROM attendance a JOIN student ON a.student_id = student.id WHERE student.id = ? ORDER BY date DESC',
            (login_user['user_id'],)
        )
        return render_template('attendance.html', records=records, role=role)

    students = query_db('SELECT * FROM student ORDER BY name')
    records = query_db('SELECT a.*, student.name, student.roll_number FROM attendance a JOIN student ON a.student_id = student.id ORDER BY date DESC')
    return render_template('attendance.html', records=records, students=students, role=role)


@app.route('/rooms', methods=['GET', 'POST'])
@login_required()
def rooms():
    role = session.get('role')
    if request.method == 'POST' and role == 'admin':
        action = request.form.get('action')
        if action == 'add':
            execute_db('INSERT INTO room_allocation (room_number, class_name, section, subject, time_slot) VALUES (?, ?, ?, ?, ?)',
                       (request.form['room_number'], request.form['class_name'], request.form['section'], request.form['subject'], request.form['time_slot']))
            flash('Room allocation added successfully.', 'success')
        elif action == 'edit':
            execute_db('UPDATE room_allocation SET room_number = ?, class_name = ?, section = ?, subject = ?, time_slot = ? WHERE id = ?',
                       (request.form['room_number'], request.form['class_name'], request.form['section'], request.form['subject'], request.form['time_slot'], request.form['id']))
            flash('Room allocation updated successfully.', 'success')
        elif action == 'delete':
            execute_db('DELETE FROM room_allocation WHERE id = ?', (request.form['id'],))
            flash('Room allocation deleted successfully.', 'success')
        return redirect(url_for('rooms'))

    allocations = query_db('SELECT * FROM room_allocation ORDER BY room_number')
    return render_template('rooms.html', allocations=allocations, role=role)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
