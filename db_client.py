import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Dict, Any
from config import db_params


class PostgresDB:
    _pool = None

    def __init__(self, host: str, database: str, user: str, password: str, port: int = 5432,
                 minconn: int = 1, maxconn: int = 10):
        if not PostgresDB._pool:
            PostgresDB._pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=host,
                database=database,
                user=user,
                password=password,
                port=port
            )

    def _get_conn(self):
        return PostgresDB._pool.getconn()

    def _release_conn(self, conn):
        PostgresDB._pool.putconn(conn)

    def execute(self, sql: str, params: Tuple = (), returning: bool = True) -> None:
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()[0] if returning else False
                conn.commit()
                return result
        finally:
            self._release_conn(conn)

    def create_table(self, create_sql: str):
        self.execute(create_sql)

    def insert(self, table: str, data: Dict[str, Any], returning: bool = True):
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            context = " RETURNING id" if returning else ""
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}){context};"
            print(sql, tuple(data.values()))
            new_id = self.execute(sql, tuple(data.values()), returning=returning)
            return new_id
        except Exception as ex:
            print(ex)
            return False

    def upsert(self, table: str, data: Dict[str, Any], conflict_field: str):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        updates = ', '.join([f"{col}=EXCLUDED.{col}" for col in data.keys() if col != conflict_field])
        sql = f"""
            INSERT INTO {table} ({columns}) 
            VALUES ({placeholders}) 
            ON CONFLICT ({conflict_field}) DO UPDATE SET {updates}
        """
        self.execute(sql, tuple(data.values()))
        return True

    def fetch_all(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        finally:
            self._release_conn(conn)

    def fetch_one(self, sql: str, params: Tuple = ()) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()
        finally:
            self._release_conn(conn)

    def close_all_connections(self):
        if PostgresDB._pool:
            PostgresDB._pool.closeall()


def main():
    db = PostgresDB(
        **db_params
    )

    # 1. USER_PROFILES
    # 1. Пользователи
    db.create_table("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            email VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            password VARCHAR NOT NULL,
            personality_type VARCHAR,
            status VARCHAR DEFAULT 'free'
        );
        """)

    # 2. Черты
    db.create_table("""
        CREATE TABLE IF NOT EXISTS traits (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE
        );
        """)

    # 3. Черты пользователя
    db.create_table("""
        CREATE TABLE IF NOT EXISTS user_traits (
            user_email VARCHAR REFERENCES user_profiles(email) ON DELETE CASCADE,
            trait_id INTEGER REFERENCES traits(id) ON DELETE CASCADE,
            value INTEGER,
            PRIMARY KEY (user_email, trait_id)
        );
        """)

    # 4. Цели пользователя
    db.create_table("""
        CREATE TABLE IF NOT EXISTS user_goals (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR REFERENCES user_profiles(email) ON DELETE CASCADE,
            goal TEXT NOT NULL
        );
        """)

    # 5. Прогресс по курсам
    db.create_table("""
        CREATE TABLE IF NOT EXISTS user_courses_progress (
            user_email VARCHAR REFERENCES user_profiles(email) ON DELETE CASCADE,
            course_id INTEGER NOT NULL,
            progress TEXT,
            PRIMARY KEY (user_email, course_id)
        );
        """)

    # 6. Пройденные тесты
    db.create_table("""
        CREATE TABLE IF NOT EXISTS user_tests_completed (
            user_email VARCHAR REFERENCES user_profiles(email) ON DELETE CASCADE,
            test_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_email, test_id)
        );
        """)

    # 2. MAIN_COURSES
    db.create_table("""
    CREATE TABLE IF NOT EXISTS main_courses (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        author TEXT,
        traits TEXT[],
        first_lesson_id VARCHAR,
        available BOOLEAN DEFAULT FALSE,
        condition TEXT
    );
    """)

    # 3. AUTHOR_COURSES
    db.create_table("""
    CREATE TABLE IF NOT EXISTS author_courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        author TEXT,
        traits TEXT[],
        first_lesson_id VARCHAR,
        available BOOLEAN DEFAULT FALSE,
        condition TEXT
    );
    """)

    # 4. LESSONS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS lessons (
        id VARCHAR PRIMARY KEY,
        course_type VARCHAR,
        course_id INTEGER,
        title TEXT,
        type VARCHAR,
        content JSONB,
        question JSONB
    );
    """)

    # 5. TESTS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS tests (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        available BOOLEAN DEFAULT FALSE,
        condition TEXT[]
    );
    """)

    # 6. TEST_QUESTIONS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS test_questions (
        test_id INTEGER REFERENCES tests(id),
        question_index SERIAL,
        text TEXT,
        options TEXT[],
        PRIMARY KEY (test_id, question_index)
    );
    """)

    # 7. ROLE_TEST_QUESTIONS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS role_test_questions (
        id SERIAL PRIMARY KEY,
        text TEXT NOT NULL,
        options TEXT[]
    );
    """)

    # 8. LEVELS_COURSE
    db.create_table("""
    CREATE TABLE IF NOT EXISTS levels_course (
        course_id INTEGER,
        level_index INTEGER,
        step_index INTEGER,
        lesson_id VARCHAR,
        title TEXT,
        description TEXT,
        color TEXT,
        size TEXT,
        PRIMARY KEY (course_id, level_index, step_index)
    );
    """)

    # 9. GUEST_EMAILS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS guest_emails (
        email VARCHAR PRIMARY KEY,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10. RESET_TOKENS
    db.create_table("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        token UUID PRIMARY KEY,
        email VARCHAR REFERENCES user_profiles(email),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("✅ Все таблицы успешно созданы.")
    db.close_all_connections()


if __name__ == "__main__":
    db = PostgresDB(
        **db_params
    )
    # db.insert('users_tests', {
    #         "user_id": 'admin@gmail.com',
    #         "test_id": 6
    #     }, returning=False)
    # db.execute("INSERT INTO users_tests (user_id, test_id) VALUES (%s, %s)", ('admin@gmail.com', 6), returning=False)
