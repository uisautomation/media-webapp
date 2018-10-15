import django.contrib.postgres.indexes
import django.contrib.postgres.search as pgsearch
from django.db import migrations, models


# Raw SQL which creates a trigger which ensures that the text search vector is updated when the
# dependent fields update.
CREATE_TRIGGER_SQL = [
    # A function intended to be run as a trigger on the mediaplatform.Channel table which will
    # update the text search vector field to contain a concatenation of the title, description and
    # tags. All of these are separated by spaces.
    r'''
    CREATE FUNCTION mediaplatform_channel_tsvectorupdate_trigger() RETURNS trigger AS $$
    begin
        new.text_search_vector :=
            to_tsvector('pg_catalog.english', concat(
                coalesce(new.title, ''),
                ' ',
                coalesce(new.description, '')
            ));
        return new;
    end
    $$ LANGUAGE plpgsql;
    ''',

    # A trigger on the mediaplatform.Channel table which updates the text search vector field if
    # the title or description change or if a new row is inserted.
    r'''
    CREATE
        TRIGGER mediaplatform_channel_tsvectorupdate
    BEFORE
        INSERT OR UPDATE OF title, description
    ON
        mediaplatform_channel
    FOR EACH ROW
        EXECUTE PROCEDURE mediaplatform_channel_tsvectorupdate_trigger();
    ''',

    # Perform a trivial update of the mediaplatform.Channel table to cause the trigger to be run
    # for each row.
    r'''
    UPDATE mediaplatform_channel SET title=title;
    ''',

    # A function intended to be run as a trigger on the mediaplatform.Playlist table which will
    # update the text search vector field to contain a concatenation of the title, description and
    # tags. All of these are separated by spaces.
    r'''
    CREATE FUNCTION mediaplatform_playlist_tsvectorupdate_trigger() RETURNS trigger AS $$
    begin
        new.text_search_vector :=
            to_tsvector('pg_catalog.english', concat(
                coalesce(new.title, ''),
                ' ',
                coalesce(new.description, '')
            ));
        return new;
    end
    $$ LANGUAGE plpgsql;
    ''',

    # A trigger on the mediaplatform.Playlist table which updates the text search vector field if
    # the title or description change or if a new row is inserted.
    r'''
    CREATE
        TRIGGER mediaplatform_playlist_tsvectorupdate
    BEFORE
        INSERT OR UPDATE OF title, description
    ON
        mediaplatform_playlist
    FOR EACH ROW
        EXECUTE PROCEDURE mediaplatform_playlist_tsvectorupdate_trigger();
    ''',

    # Perform a trivial update of the mediaplatform.Playlist table to cause the trigger to be run
    # for each row.
    r'''
    UPDATE mediaplatform_playlist SET title=title;
    ''',
]

# Drop the trigger and trigger function created by CREATE_TRIGGER_SQL.
DROP_TRIGGER_SQL = [
    r'''
    DROP TRIGGER mediaplatform_channel_tsvectorupdate ON mediaplatform_channel;
    ''',
    r'''
    DROP FUNCTION mediaplatform_channel_tsvectorupdate_trigger;
    ''',
    r'''
    DROP TRIGGER mediaplatform_playlist_tsvectorupdate ON mediaplatform_playlist;
    ''',
    r'''
    DROP FUNCTION mediaplatform_playlist_tsvectorupdate_trigger;
    ''',
]


class Migration(migrations.Migration):

    dependencies = [
        ('mediaplatform', '0018_add_full_text_search'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='text_search_vector',
            field=django.contrib.postgres.search.SearchVectorField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='playlist',
            name='text_search_vector',
            field=django.contrib.postgres.search.SearchVectorField(default=''),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['updated_at'], name='mediaplatfo_updated_be3f05_idx'),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['text_search_vector'], name='mediaplatfo_text_se_333a10_gin'),
        ),
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['updated_at'], name='mediaplatfo_updated_c5a2bd_idx'),
        ),
        migrations.AddIndex(
            model_name='playlist',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['text_search_vector'], name='mediaplatfo_text_se_0a603a_gin'),
        ),
        migrations.RunSQL(CREATE_TRIGGER_SQL, DROP_TRIGGER_SQL),
    ]
