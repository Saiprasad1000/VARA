import os
import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Vara.settings")
django.setup()

def drop_tables():
    with connection.cursor() as cursor:
        tables = [
            'socialaccount_socialtoken',
            'socialaccount_socialaccount',
            'socialaccount_socialapp_sites',
            'socialaccount_socialapp',
        ]
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")

if __name__ == "__main__":
    drop_tables()
