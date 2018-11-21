"""
Handling of timezone-aware date time objects.

"""
import pytz


def datetime_as_utcdatetime(dt):
    """
    Return a timezone-aware datetime as a UTCdatetime as specified in
    https://www.openarchives.org/OAI/openarchivesprotocol.html#Dates, §3.3.

    Note that the OAI-PMH specifcation mandates that the "Z" (zulu) specifier be used for the
    timezone as opposed to the equally valid "+00.00".

    """
    # Convert to UTC
    utc_dt = dt.astimezone(pytz.utc)

    # Format appropriately
    return f'{utc_dt:%Y-%m-%dT%H:%M:%S}Z'
