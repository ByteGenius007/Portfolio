import sqlite3
from config1 import DATABASE

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]
statuses = [ (_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]
conn = sqlite3.connect("database.db")  # Укажи правильный путь к БД
cursor = conn.cursor()


class DB_Manager:
    def __init__(self, database):
        self.database = database
        self.connection = sqlite3.connect(self.database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def create_tables(self):
        with self.connection:
            self.cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status_name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_name TEXT NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE,
                    status_id INTEGER NOT NULL,
                    photo_path TEXT,
                    c
                    reated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (status_id) REFERENCES status(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS project_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    skill_id INTEGER NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
                );
            ''')

    # def add_photo_column(self):
    #     with self.connection:
    #         self.cursor.execute("PRAGMA table_info(projects)")
    #         columns = [row[1] for row in self.cursor.fetchall()]
    #         if "photo" not in columns:
    #             self.cursor.execute("ALTER TABLE projects ADD COLUMN photo TEXT DEFAULT 'default_photo.jpg'")

    def update_project_photo(self, project_name, user_id, file_path):
        # SQL-запрос для обновления фото проекта
        query = "UPDATE projects SET photo_path = ? WHERE project_name = ? AND user_id = ?"
        self.cursor.execute(query, (file_path, project_name, user_id))
        self.connection.commit()

    def __executemany(self, sql, data):
        with self.connection:
            self.cursor.executemany(sql, data)

    def __select_data(self, sql, data=tuple()):
        self.cursor.execute(sql, data)
        return self.cursor.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        self.__executemany(sql, skills)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        self.__executemany(sql, statuses)

    def insert_project(self, data):
        sql = "INSERT INTO projects (user_id, project_name, description, url, status_id) VALUES (?, ?, ?, ?, ?)"
        self.__executemany(sql, data)

    def get_status_id(self,status_name):
        sql = "SELECT id FROM status WHERE status_name = ?"
        result = self.__select_data(sql, (status_name,))
        return result[0][0] if result else None
    
    def get_status_name(self, status_id):
        self.cursor.execute("SELECT status_name FROM status WHERE id = ?", (status_id,))
        status = self.cursor.fetchone()
        return status[0] if status else "Неизвестный статус"


    def get_project_id(self, project_name, user_id):
        query = "SELECT id FROM projects WHERE project_name = ? AND user_id = ?"
        self.cursor.execute(query, (project_name, user_id))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_project_skills(self, project_id):
        query = """
        SELECT skills.skill_name FROM skills
        INNER JOIN project_skills ON skills.id = project_skills.skill_id
        WHERE project_skills.project_id = ?
    """
        self.cursor.execute(query, (project_id,))
        return [row[0] for row in self.cursor.fetchall()]


    def get_skill_id(self, skill_name):
        query = "SELECT id FROM skills WHERE skill_name = ?"
        self.cursor.execute(query, (skill_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_skills(self):
        sql = "SELECT id, skill_name FROM skills"
        return self.__select_data(sql)

    def insert_skill(self, project_id, skill_id):
        sql = "INSERT INTO project_skills (project_id, skill_id) VALUES (?, ?)"
        self.__executemany(sql, [(project_id, skill_id)])

    def get_statuses(self):
        sql = "SELECT id, status_name FROM status"
        return self.__select_data(sql)

    def get_projects(self, user_id):
        sql = "SELECT * FROM projects WHERE user_id = ?"
        return self.__select_data(sql, (user_id,))
    
    def get_current_status(self, project_name, user_id):
        sql = "SELECT status_id FROM projects WHERE project_name = ? AND user_id = ?"
        result = self.__select_data(sql, (project_name, user_id))
        return result[0][0] if result else None

    def check_project_exists(self, project_name, user_id):
        sql = "SELECT id FROM projects WHERE project_name = ? AND user_id = ?"
        result = self.__select_data(sql, (project_name, user_id))
        return result  # Если пусто, значит такого проекта нет

    def update_projects(self, param, data):
        sql = f"UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?"
        with self.connection:
            self.cursor.execute(sql, data)

    # def update_projects(self, param, data):
    #     sql = f"UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?"
    #     self.__executemany(sql, [data])

    def get_project_info(self, user_id, project_name):
        sql = "SELECT * FROM projects WHERE user_id = ? AND project_name = ?"
        return self.__select_data(sql, (user_id, project_name))
    
    def delete_project(self, user_id, project_id):
        sql = "DELETE FROM projects WHERE user_id = ? AND id = ?"
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        sql = "DELETE FROM project_skills WHERE project_id = ? AND skill_id = ?"
        self.__executemany(sql, [(project_id, skill_id)])

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.default_insert()
    cursor.execute("SELECT photo_path FROM projects WHERE name = ?", ("lol",))
    result = cursor.fetchone()

    print("Photo path:", result)

    conn.close()
