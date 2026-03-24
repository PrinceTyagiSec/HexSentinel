from gui.home import start_app
from core.database import init_db, insert_sample_data

if __name__ == "__main__":
    init_db()
    insert_sample_data()
    start_app()