CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    student_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    program TEXT NOT NULL,
    academic_level TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    biography TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    course_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    semester TEXT NOT NULL,

    FOREIGN KEY (student_id)
        REFERENCES students (id) ON DELETE CASCADE,

    FOREIGN KEY (course_id)
        REFERENCES courses (id) ON DELETE RESTRICT,

    UNIQUE (student_id, course_id, semester)
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL UNIQUE,
    score REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
    letter_grade TEXT NOT NULL CHECK (
        letter_grade IN (
            'A', 'A-', 'B+', 'B', 'B-',
            'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'
        )
    ),

    FOREIGN KEY (enrollment_id)
        REFERENCES enrollments (id) ON DELETE CASCADE
);