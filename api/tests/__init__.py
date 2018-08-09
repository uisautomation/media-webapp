from django.db import connection


def create_stats_table():
    """
    Create a mock stats table in the database.

    """
    with connection.cursor() as cursor:
        cursor.execute('CREATE SCHEMA stats')
        cursor.execute('''
            CREATE TABLE stats.media_stats_by_day (
              id                SERIAL PRIMARY KEY,
              media_id          BIGINT,
              day               DATE,
              num_hits          BIGINT
            )''')


def delete_stats_table():
    """
    Drop the mock stats table from the datavase

    """
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE stats.media_stats_by_day')
        cursor.execute('DROP SCHEMA stats')


def add_stat(day, num_hits, media_id):
    """Add an individual statistics to the mock stats table."""
    with connection.cursor() as cursor:
        cursor.execute('''
            INSERT INTO stats.media_stats_by_day (
                day, num_hits, media_id
            ) VALUES (%s, %s, %s)
        ''', (day, num_hits, media_id))
