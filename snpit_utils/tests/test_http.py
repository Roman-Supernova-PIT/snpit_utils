import pytest
import psycopg
from snpit_utils.http import retry_post


def test_retry_post( dbclient ):
    provstodel = []
    try:
        res = retry_post( 'https://webserver:8080/test/blah', verify=False )
        data = res.json()
        assert isinstance( data, dict )
        assert set( data.keys() ) == { 'param' }
        assert data['param'] == 'blah'

        res = retry_post( 'https://webserver:8080/test/blah', { 'answer': 42 }, verify=False )
        data = res.json()
        assert isinstance( data, dict )
        assert set( data.keys() ) == { 'param', 'json' }
        assert data['param'] == 'blah'
        assert data['json']['answer'] == 42

        with pytest.raises( RuntimeError, match="Got status 500 trying to connect" ):
            retry_post( 'https://webserver:8080/this_endpoint_does_not_exist', retries=3, initsleep=0.2, verify=False )

    finally:
        with open( '/secrets/pgpasswd' ) as ifp:
            pw = ifp.readline().strip()
        with psycopg.connect( dbname="roman_snpit", user="postgres", password=pw, host="postgres", port=5432 ) as con:
            cursor = con.cursor()
            cursor.execute( "DELETE FROM provenance_tag WHERE tag='bar'" )
            cursor.execute( "DELETE FROM provenance WHERE id=ANY(%(provs)s)", { 'provs': provstodel } )
            con.commit()
