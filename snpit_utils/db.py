import base64
import hashlib
import simplejson
import uuid


from rkwebutil.rkauth_client import rkAuthClient

from snpit_utils.config import Config


class SNPITDBClient( rkAuthClient ):
    def __init__( self, url=None, username=None, password=None, passwordfile=None, verify=True ):
        cfg = Config.get()
        url = url if url is not None else cfg.value( 'db.url' )
        username = username if username is not None else cfg.value( 'db.username' )
        if ( password is None ) and ( passwordfile is None ):
            try:
                password = cfg.value( 'db.password' )
            except Exception:
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

class Provenance:
    def __init__( self, process, major, minor, params={}, environment=None, env_major=None, env_minor=None,
                  upstreams=[] ):
        """Instantiate a Provenance

        Once instantiated, will have a property id that holds the UUID
        for this provenance.  This UUID is defined from a md5 hash of
        all the arguments, so will be the same every time you pass the
        same arguments.  (It's convenient that md5sums and UUIDs are
        both 128-bit numbers.)

        Parmaeters
        ----------
          process : str
            The name of the process, e.g. "phrosty", "campari", "import_rapid_alert", etc.

          major : int
            Semantic major version of the code described by process.

          minor : int
            Semantic minor version of the code described by process.

          params : dict, default {}
            Parameters that uniquely define process. This should include
            all parameters that would be the same for all runs on one
            set of data.  So, for instance, for difference imaging
            transient detection software, you would *not* include the
            name of the science image or the name of the transient.
            However, you would include things like configuration
            parameters to SFFT, detection thresholds, and the name and
            parameters of however you decided to figure out which
            template image to use.

          environment : int, default None
            Which SNPIT environment did the process use?  TODO: this
            still need to be defined.

          env_major : int, default None
            Semantic major version of environment.

          env_minor : int, default None
            Semantic minor version of environment.

          upstreams : list of UUID or Provenance
            Upstream provenances to this provenance

        """
        self.process = process
        self.major = major
        self.minor = minor
        self.params = params
        self.environment = environment
        self.env_major = env_major
        self.env_minor = env_minor
        self.upstream_ids = [ i if isinstance(i, uuid.UUID) else i.id for i in upstreams ]
        self.update_id()

    def spec_dict( self ):
        return { 'process': self.process,
                 'major': self.major,
                 'minor': self.minor,
                 'environment': self.environment,
                 'env_major': self.env_major,
                 'env_minor': self.env_minor,
                 'params': self.params,
                 'upstream_ids': [ str(i) for i in self.upstream_ids ]
                }


    def update_id( self ):
        """Update self.id based on stored properties.

        If you change any of the properties of the object that define
        the Provenance, you must call this to make the id property
        correct.  Probably this is a bad idea; you should view
        Provenance objects as immutable and not change them after you
        make them.

        """
        spec = simplejson.dumps( self.spec_dict() ).encode( "utf-8" )
        barf = base64.standard_b64encode( spec )
        md5sum = hashlib.md5( barf )
        self.id = uuid.UUID( md5sum.hexdigest() )


    def save_to_db( self, dbclient, tag=None, replace_tag=False, exists=None ):
        """Save this provenance to the database.

        Will call self.update_id() as a side effect, just to make sure
        the right ID is saved to the database.

        Parmaeters
        ----------
          dbclient: snpit_utils.db.SNPITDBClient
            This is needed to talk to the Roman SNPIT database web server.

          tag : str, default None
            Add this provenance to this provenance tag for this process.

          replace_tag : bool, default False
            Ignored if tag is None.  If tag is set, but a provenance
            already exists for this process and tag, then normally
            that's an error.  If replace_tag is True, delete the old
            provenance associated with the tag and set the new
            provenance.

          exists : bool, default None
            If None, and the provenance already exists in the database,
            do nothing.  If False, and the provenance already exists in
            the database, raise an exception.  If True, and the
            provenance doesn't already exist in the database, raise an
            exception.  It doesn't make a lot of sense, usually, to call
            this method with exists=True.

        """

        self.update_id()
        savedprov = self.get_by_id( dbclient, self.id )

        if ( savedprov is None ) and ( exists is not None ) and exists:
            raise RuntimeError( f"Provenance {self.id} doesn't exist in the database, and exists is True; "
                                f"why are you calling save_to_db???" )
        if ( savedprov is not None ) and ( exists is not None ) and ( not exists ):
            raise RuntimeError( f"Error saving provenance {self.id}; it already exists in the database." )

        if savedprov is None:
            res = dbclient.send( "createprovenance",
                                 { 'id': self.id,
                                   'process': self.process,
                                   'major': self.major,
                                   'minor': self.minor,
                                   'environment': self.environment,
                                   'env_major': self.env_major,
                                   'env_minor': self.env_minor,
                                   'params': self.params,
                                   'upstream_ids': self.upstream_ids,
                                   'tag': tag,
                                   'replace_tag': replace_tag } )
            if res['status'] != 'ok':
                raise RuntimeError( f"Something went wrong saving provenance {self.id} to the databse." )


    @classmethod
    def get( cls, dbclient, process, major, minor, params={}, environment=None, env_major=None, env_minor=None,
             exists=None, savetodb=False ):
        """Get a Provenance based on properties.

        Arguments are the same as are passed to the Provenance constructor, plus:

        Parameters
        ----------
          dbclient: snpit_utils.db.SNPITDBClient
            This is needed to talk to the Roman SNPIT database web server.

          process, major, minor, params, environment, env_major, env_minor : varied
            These are the same as what's passed to the Provenance constructor

          exists : bool, default None
            Normally, you get back the provenance you ask for.  (This
            is, depending on savetodb, just the same as instantiating a
            Provenance object.)  However, if exists is True, then it
            will raise an exception if the provenance isn't already
            saved to the database.  If exists is False, then it will
            raise an exception if the provenance *is* already saved to
            the database.  (Setting exists=False mostly only makes sense
            when setting savetodb to True.)

          savetodb : bool, default False
            By default, you get the Provenance you ask for, but
            thedatabse is not changed.  Set this to True to save the
            provenance to the database.  If savetodb is True and exists
            is True, then nothing is saved, because either the
            provenance already exists, or an exception was raised.  If
            savetodb is True and exists is None, then the provenance
            will be saved to the database if it doesn't already exist.
            If savetodb is True and exists is False, an exception will
            be raised if the provenance is already in the database,
            otherwise the new provenance will be saved.

        """

        prov = cls( process, major, minor, params=params, environment=environment,
                    env_major=env_major, env_minor=env_minor )
        if savetodb:
            try:
                prov.save_to_db( dbclient, exists=exists )
            except Exception:
                if ( exists is not None ) and ( not exists ):
                    raise
                # Otherwise, the exception just means it was already there, so we don't care

        return prov


    @classmethod
    def get_by_id( cls, dbclient, provid ):
        """Return a Provenance pulled from the database.

        Raises an exception if it does not exist.

        Parameters
        ----------
          dbclient: snpit_utils.db.SNPITDBClient
            This is needed to talk to the Roman SNPIT database web server.

          provid: UUID
             The ID to fetch

        """

        return dbclient.send( f"getprovenance/{provid}" )
