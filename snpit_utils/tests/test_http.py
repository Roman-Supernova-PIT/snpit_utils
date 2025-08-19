from snpit_utils.http import retry_post


def test_retry_post():
    # Really testing this without putting up a custom webserver designed specifically for the test
    #   is hard....  In particular, testing the retry/fail part.  Eventually we may need to write
    #   that custom webserver to test this, but for now just test that the basic post functionality
    #   works by posting to the roman-simdex server whose answers we know.

    res = retry_post( 'https://roman-desc-simdex.lbl.gov/findtransients/id=30011289' )
    data = res.json()
    assert isinstance( data, dict )
    assert len( data['id'] ) == 1
    assert data['id'][0] == 30011289

    res = retry_post( 'https://roman-desc-simdex.lbl.gov/findtransients', json={ 'id': 30011289 } )
    data = res.json()
    assert isinstance( data, dict )
    assert len( data['id'] ) == 1
    assert data['id'][0] == 30011289
