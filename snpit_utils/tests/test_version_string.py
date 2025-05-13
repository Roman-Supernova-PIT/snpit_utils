def test_version_is_string():
    from snpit_utils import __version__
    assert isinstance(__version__, str)
