PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_number TEXT NOT NULL UNIQUE,
    class_name TEXT NOT NULL,
    section TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    classes_taught TEXT NOT NULL,
    subjects_taught TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS section_subject_teacher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL,
    subject TEXT NOT NULL,
    teacher_id INTEGER NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS student_fee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Paid', 'Pending')),
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS teacher_salary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Paid', 'Pending')),
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS room_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT NOT NULL,
    class_name TEXT NOT NULL,
    section TEXT NOT NULL,
    subject TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    UNIQUE(room_number, time_slot)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS login (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
    user_id INTEGER
);

INSERT OR IGNORE INTO admin (name, email) VALUES
('School Administrator', 'admin@school.com');

INSERT OR IGNORE INTO student (name, roll_number, class_name, section, email) VALUES
('John Doe', 'S1001', '10', 'A', 'john@student.com'),
('Jane Smith', 'S1002', '10', 'B', 'jane@student.com');

INSERT OR IGNORE INTO staff (name, classes_taught, subjects_taught, email) VALUES
('Mr. Khan', '10', 'Math', 'khan@school.com'),
('Ms. Patel', '10', 'Science', 'patel@school.com');

INSERT OR IGNORE INTO section_subject_teacher (section, subject, teacher_id) VALUES
('A', 'Math', 1),
('B', 'Science', 2);

INSERT OR IGNORE INTO student_fee (student_id, amount, payment_date, status) VALUES
(1, 500.00, '2026-04-01', 'Paid'),
(2, 500.00, '2026-04-01', 'Pending');

INSERT OR IGNORE INTO teacher_salary (staff_id, amount, payment_date, status) VALUES
(1, 1200.00, '2026-04-01', 'Paid'),
(2, 1250.00, '2026-04-01', 'Pending');

INSERT OR IGNORE INTO room_allocation (room_number, class_name, section, subject, time_slot) VALUES
('101', '10', 'A', 'Math', '09:00-10:00'),
('102', '10', 'B', 'Science', '10:00-11:00');

INSERT OR IGNORE INTO login (username, password, role, user_id) VALUES
('admin', 'admin', 'admin', NULL),
('john@student.com', 'password', 'student', 1),
('jane@student.com', 'password', 'student', 2);
