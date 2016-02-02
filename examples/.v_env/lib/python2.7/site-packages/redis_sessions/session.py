import redis

try:
    from django.utils.encoding import force_unicode
except ImportError:  # Python 3.*
    from django.utils.encoding import force_text as force_unicode
from django.contrib.sessions.backends.base import SessionBase, CreateError
from redis_sessions import settings


# Avoid new redis connection on each request

if settings.SESSION_REDIS_SENTINEL_LIST is not None:
    from redis.sentinel import Sentinel

    redis_server = Sentinel(settings.SESSION_REDIS_SENTINEL_LIST, socket_timeout=0.1) \
                    .master_for(settings.SESSION_REDIS_SENTINEL_MASTER_ALIAS, 
                                socket_timeout=0.1, 
                                db=getattr(settings, 'SESSION_REDIS_DB', 0))

elif settings.SESSION_REDIS_URL is not None:

    redis_server = redis.StrictRedis.from_url(settings.SESSION_REDIS_URL)
elif settings.SESSION_REDIS_UNIX_DOMAIN_SOCKET_PATH is None:
    
    redis_server = redis.StrictRedis(
        host=settings.SESSION_REDIS_HOST,
        port=settings.SESSION_REDIS_PORT,
        db=settings.SESSION_REDIS_DB,
        password=settings.SESSION_REDIS_PASSWORD
    )
else:

    redis_server = redis.StrictRedis(
        unix_socket_path=settings.SESSION_REDIS_UNIX_DOMAIN_SOCKET_PATH,
        db=settings.SESSION_REDIS_DB,
        password=settings.SESSION_REDIS_PASSWORD,
    )


class SessionStore(SessionBase):
    """
    Implements Redis database session store.
    """
    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)

        self.server = redis_server

    def load(self):
        try:
            session_data = self.server.get(
                self.get_real_stored_key(self._get_or_create_session_key())
            )
            return self.decode(force_unicode(session_data))
        except:
            self._session_key = None
            return {}

    def exists(self, session_key):
        return self.server.exists(self.get_real_stored_key(session_key))

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()

            try:
                self.save(must_create=True)
            except CreateError:
                # Key wasn't unique. Try again.
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        if must_create and self.exists(self._get_or_create_session_key()):
            raise CreateError
        data = self.encode(self._get_session(no_load=must_create))
        if redis.VERSION[0] >= 2:
            self.server.setex(
                self.get_real_stored_key(self._get_or_create_session_key()),
                self.get_expiry_age(),
                data
            )
        else:
            self.server.set(
                self.get_real_stored_key(self._get_or_create_session_key()),
                data
            )
            self.server.expire(
                self.get_real_stored_key(self._get_or_create_session_key()),
                self.get_expiry_age()
            )

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        try:
            self.server.delete(self.get_real_stored_key(session_key))
        except:
            pass

    def get_real_stored_key(self, session_key):
        """Return the real key name in redis storage
        @return string
        """
        prefix = settings.SESSION_REDIS_PREFIX
        if not prefix:
            return session_key
        return ':'.join([prefix, session_key])
