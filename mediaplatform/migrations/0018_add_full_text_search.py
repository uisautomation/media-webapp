import django.contrib.postgres.indexes
import django.contrib.postgres.search as pgsearch
from django.db import migrations


# Raw SQL which creates a trigger which ensures that the text search vector is updated when the
# dependent fields update.
CREATE_TRIGGER_SQL = [
    # A function intended to be run as a trigger on the mediaplatform.MediaItem table which will
    # update the text search vector field to contain a concatenation of the title, description and
    # tags. All of these are separated by spaces.
    r'''
    CREATE FUNCTION mediaplatform_mediaitem_tsvectorupdate_trigger() RETURNS trigger AS $$
    begin
        new.text_search_vector :=
            to_tsvector('pg_catalog.english', concat(
                coalesce(new.title, ''),
                ' ',
                coalesce(new.description, ''),
                ' ',
                array_to_string(new.tags, ' ')
            ));
        return new;
    end
    $$ LANGUAGE plpgsql;
    ''',

    # A trigger on the mediaplatform.MediaItem table which updates the text search vector field if
    # the title, description or tags change or if a new row is inserted.
    r'''
    CREATE
        TRIGGER mediaplatform_mediaitem_tsvectorupdate
    BEFORE
        INSERT OR UPDATE OF title, description, tags
    ON
        mediaplatform_mediaitem
    FOR EACH ROW
        EXECUTE PROCEDURE mediaplatform_mediaitem_tsvectorupdate_trigger();
    ''',

    # Perform a trivial update of the mediaplatform.MediaItem table to cause the trigger to be run
    # for each row.
    r'''
    UPDATE mediaplatform_mediaitem SET title=title;
    ''',
]

# Drop the trigger and trigger function created by CREATE_TRIGGER_SQL.
DROP_TRIGGER_SQL = [
    r'''
    DROP TRIGGER mediaplatform_mediaitem_tsvectorupdate ON mediaplatform_mediaitem;
    ''',
    r'''
    DROP FUNCTION mediaplatform_mediaitem_tsvectorupdate_trigger;
    ''',
]


class Migration(migrations.Migration):

    dependencies = [
        ('mediaplatform', '0017_index_media_item_updated_at_and_published_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaitem',
            name='text_search_vector',
            field=django.contrib.postgres.search.SearchVectorField(default=''),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='mediaitem',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['text_search_vector'], name='mediaplatfo_text_se_d418e1_gin'
            ),
        ),
        migrations.RunSQL(CREATE_TRIGGER_SQL, DROP_TRIGGER_SQL),
    ]
