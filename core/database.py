import psycopg2
from segredo import DATABASE_URL
import os


# DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)


