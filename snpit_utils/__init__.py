from importlib.metadata import version, PackageNotFoundError
__all__ = []



try:
    __version__ = version("snpit_utils")
except PackageNotFoundError:
    # package is not installed
    pass
