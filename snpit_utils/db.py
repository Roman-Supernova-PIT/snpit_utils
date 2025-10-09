from rkwebutils.rkauth_client import rkAuthClient

from snpit_utils.config import Config


class SNPITDBClient( rkAuthClient ):
    def __init__( self, url=None, username=None, password=None, passwordfile=None, verify=True ):
        cfg = Config.get()
        url = url if url is not None else cfg.value( 'db.url' )
        username = username if username is not None else cfg.value( 'db.username' )
        if ( password is None ) and ( passwordfile is None ):
            try:
                password = cfg.value( 'db.password' )
            except:
                password = None
            if password is None:
                with open( cfg.value( 'db.passwordfile' ) ) as ifp:
                    password = ifp.readline().strip()
        else:
            if password is None:
                with open( passwordfile ) as ifp:
                    password = ifp.readline.strip()

        super().__init__( url, username, password, verify=verify )


# ======================================================================
        
class Provrenance:
    def __init__():
        self.
