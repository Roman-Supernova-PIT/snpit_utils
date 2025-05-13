import pytest
import sys
import io
import re
import logging
import multiprocessing.pool

import snpit_utils.logger
from snpit_utils.logger import SNLogger


@pytest.fixture( autouse=True )
def reset_snlogger():
    """Reset the snlogger singleton after each test.

    This isn't really a full reset, because it doesn't delete the
    created logging.Logger objects, nor does it reset SNLogger._ordinal
    (which you need if you don't delete the created logging.Logger
    objects and logging's cache of them).

    """
    try:
        yield True
    finally:
        SNLogger._instance = None


@pytest.fixture
def logoutput():
    """Configure the SNLogger to log to a io.StringIO, and return that StringIO.

    Use this to see the output produced by the logger.

    I haven't figured out how to test SNLogger logging to stderr.  I
    tried resetting sys.stderr to a stream I controlled, but that didn't
    work. I suspect pytest is already doing fancy things with
    sys.stderr, and trying to do something inside with sys.stderr
    requires more understanding of what's going on in pytest.

    """
    logstream = io.StringIO()
    handler = logging.StreamHandler( logstream )
    SNLogger.instance( handler=handler )
    return logstream


def default_regex( message ):
    return r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\ - (.*)\] - ' + message + '$'


def test_instance():
    logger = SNLogger.instance()
    assert isinstance( logger, SNLogger )
    assert isinstance( logger._logger, logging.Logger )


def test_get():
    loggingobj = SNLogger.get()
    assert isinstance( loggingobj, logging.Logger )
    assert loggingobj == SNLogger._instance._logger


def test_set_level( logoutput ):
    """Make sure log levels are set properly.

    Also does a baic test of SNLogger.debug, SNLogger.info,
    SNLogger.warning, SNLogger.error, and SNLogger.critical.

    """

    levels = [ 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' ]
    funcs = [ SNLogger.debug, SNLogger.info, SNLogger.warning, SNLogger.error, SNLogger.critical ]

    for i in range( len(levels) ):
        SNLogger.set_level( getattr( logging, levels[i] ) )

        for j in range( i ):
            logoutput.seek( 0 )
            logoutput.truncate( 0 )
            funcs[j]( "Hello, world!" )
            assert len( logoutput.getvalue() ) == 0

        for j in range( i+1, len(funcs) ):
            logoutput.seek( 0 )
            logoutput.truncate( 0 )
            funcs[j]( "Hello, world!" )
            mat = re.search( default_regex( "Hello, world!" ), logoutput.getvalue() )
            assert mat is not None
            assert mat.group(1) == levels[j]


def test_exception( logoutput ):
    try:
        raise RuntimeError("uh oh")
    except RuntimeError as e:
        SNLogger.exception( e )

    assert re.search( ( r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\ - ERROR\] - uh oh\n'
                        r'Traceback \(most recent call last\):\n' ),
                      logoutput.getvalue() )


def test_replace( logoutput ):
    """Also, effectively, tests __init__."""

    # Send a starting message that should match the defaults
    SNLogger.error( "Hello, world!" )
    assert re.search( default_regex( "Hello, world!" ), logoutput.getvalue() )

    logoutput.seek(0)
    logoutput.truncate( 0 )

    # Change dateformat
    SNLogger.replace( datefmt='%b %d, %Y %H:%M:%S' )
    SNLogger.error( "Hello, world!" )
    assert re.search( r'^\[[A-Za-z]{3} \d{1,2}, \d{4} \d{2}:\d{2}:\d{2} - ERROR\] - Hello, world!$',
                      logoutput.getvalue() )
    # Reset it
    SNLogger.replace( datefmt=snpit_utils.logger._default_datefmt )

    # Change millisec
    logoutput.seek( 0 )
    logoutput.truncate( 0 )
    SNLogger.replace( show_millisec=True )
    SNLogger.error( "Hello, world!" )
    assert re.search( r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\ - (.*)\] - Hello, world!$',
                      logoutput.getvalue() )
    # Reset it
    SNLogger.replace( show_millisec=snpit_utils.logger._show_millisec )

    # Change handler
    logoutput.seek( 0 )
    logoutput.truncate( 0 )
    newstream = io.StringIO()
    handler = logging.StreamHandler( newstream )
    SNLogger.replace( handler = handler )
    SNLogger.error( "Hello, world!" )
    assert len( logoutput.getvalue() ) == 0
    assert re.search( default_regex( "Hello, world!" ), newstream.getvalue() )


def look_at_logger():
    me = multiprocessing.current_process()
    # Because of issues with capturing sys.stderr, we can't test
    #   use of multiprocessing_replace() with no arguments.  Hopefully
    #   it works...!  (Empirically: it does.)
    with pytest.raises( RuntimeError, match="If you use multiprocessing_replace and you aren't" ):
        SNLogger.multiprocessing_replace()
    mat = re.search( '([0-9]+)', me.name )
    numstr = f'{mat.group(1):>3s}' if mat is not None else str(me.pid)
    strio = io.StringIO()
    handler = logging.StreamHandler( strio )
    SNLogger.multiprocessing_replace( handler=handler )
    SNLogger.error( f"Hello from process {me.name}" )
    mat = re.search( r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\ - (.*) - ERROR\] - Hello from process (.*)$',
                       strio.getvalue() )
    return ( ( mat is not None ) and
             ( mat.group(1) == numstr ) and
             ( mat.group(2) == me.name ) )


def test_multiprocessing_replace( logoutput ):
    results = []

    def oops( e ):
        sys.stderr.write( f"Exception from subprocess: {e}\n" )
        results.append( False )

    def accumulate( worked ):
        results.append( worked )

    with multiprocessing.pool.Pool(5) as pool:
        for i in range(5):
            pool.apply_async( look_at_logger, [], {}, accumulate, oops )

        pool.close()
        pool.join()

    assert len(results) == 5
    assert all( results )
