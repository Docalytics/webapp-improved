from ndb import model

from webapp2_extras import security

from experimental import auth
from experimental.appengine.ndb import unique_model


class User(model.Model):
    """"""

    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    # Display name: username as typed by the user.
    name = model.StringProperty(required=True)
    # Username in lower case. UNIQUE.
    username = model.StringProperty(required=True)
    # ID for third party authentication, e.g. 'google:username'. UNIQUE.
    auth_id = model.StringProperty(required=True)
    # Hashed password. Can be null because third party authentication
    # doesn't have a password.
    password = model.StringProperty()
    # Primary email address. UNIQUE.
    email = model.StringProperty(required=True)
    # Account status:
    # 0: not confirmed account
    # 1: normal user
    # 2: admin
    # 3 etc: to be defined
    status = model.IntegerProperty(default=0)

    @classmethod
    def get_key(cls, username):
        return model.Key(cls, username.lower())

    @property
    def is_admin(self):
        return self.status == 2

    @property
    def is_active(self):
        return self.status != 0

    @classmethod
    def get_by_username(cls, username):
        key = cls.get_key(username)
        return key.get()

    @classmethod
    def get_by_auth_id(cls, auth_id):
        query = cls.query(cls.auth_id == auth_id)
        return query.get()

    @classmethod
    def get_by_email(cls, email):
        query = cls.query(cls.email == email)
        return query.get()

    @classmethod
    def get_by_auth_token(cls, username, token):
        token_key = UserToken.get_key(username, 'auth', token)
        user_key = cls.get_key(username)
        # Use get_multi() to save a RPC call.
        valid_token, user = model.get_multi([token_key, user_key])
        if valid_token and user:
            return user

    @classmethod
    def get_by_auth_password(cls, username, password):
        """Returns user, validating password.

        :raises:
            ``auth.InvalidUsernameError`` or ``auth.InvalidPasswordError``.
        """
        user = cls.get_by_username(username)
        if not user:
            raise auth.InvalidUsernameError()

        if not security.check_password_hash(password, user.password):
            raise auth.InvalidPasswordError()

        return user

    @classmethod
    def validate_token(cls, username, subject, token):
        rv = UserToken.get(username=username, subject=subject, token=token)
        return rv is not None

    @classmethod
    def create_auth_token(cls, username):
        entity = UserToken.create(username, 'auth', token_size=64)
        return entity.token

    @classmethod
    def validate_auth_token(cls, username, token):
        return cls.validate_token(username, 'auth', token)

    @classmethod
    def delete_auth_token(cls, username, token):
        UserToken.get_key(username, 'auth', token).delete()

    @classmethod
    def create_signup_token(cls, username):
        entity = UserToken.create(username, 'signup')
        return entity.token

    @classmethod
    def validate_signup_token(cls, username, token):
        return cls.validate_token(username, 'signup', token)

    @classmethod
    def delete_signup_token(cls, username, token):
        UserToken.get_key(username, 'signup', token).delete()

    @classmethod
    def create_user(cls, _unique_email=True, **user_values):
        """Creates a new user.

        :param _unique_email:
            True to require the email to be unique, False otherwise.
        :param user_values:
            Keyword arguments to create a new user entity. Required ones are:

            - name
            - username
            - auth_id
            - email

            Optional keywords:

            - password_raw (a plain password to be hashed)
            - status

            The properties values of `username` and `auth_id` must be unique.
            Optionally, `email` can also be required to be unique.
        :returns:
            A tuple (boolean, info). The boolean indicates if the user
            was created. If creation succeeds,  ``info`` is the user entity;
            otherwise it is a list of duplicated unique properties that
            caused the creation to fail.
        """
        assert user_values.get('password') is None, \
            'Use password_raw instead of password to create new users'

        if 'password_raw' in user_values:
            user_values['password'] = security.create_password_hash(
                user_values.pop('password_raw'), length=12)

        username = user_values['username'].lower()
        user = User(key=cls.get_key(username), **user_values)

        # Unique auth id and email.
        unique_auth_id = 'User.auth_id:%s' % user_values['auth_id']
        uniques = [unique_auth_id]
        if _unique_email:
            unique_email = 'User.email:%s' % user_values['email']
            uniques.append(unique_email)
        else:
            unique_email = None

        if uniques:
            success, existing = unique_model.Unique.create_multi(uniques)

        if success:
            txn = lambda: user.put() if not user.key.get() else None
            if model.transaction(txn):
                return True, user
            else:
                unique_model.Unique.delete_multi(uniques)
                return False, ['username']
        else:
            properties = []
            if unique_auth_id in uniques:
                properties.append('auth_id')

            if unique_email in uniques:
                properties.append('email')

            return False, properties


class UserToken(model.Model):
    """Stores validation tokens for users."""

    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    username = model.StringProperty(required=True, indexed=False)
    subject = model.StringProperty(required=True)
    token = model.StringProperty(required=True)

    @classmethod
    def get_key(cls, username, subject, token):
        """Returns a token key."""
        return model.Key(cls, '%s.%s.%s' % (username, subject, token))

    @classmethod
    def create(cls, username, subject, token=None, token_size=32):
        """Fetches a user token."""
        token = token or security.create_token(token_size)
        key = cls.get_key(username, subject, token)
        entity = cls(key=key, username=username, subject=subject, token=token)
        entity.put()
        return entity

    @classmethod
    def get(cls, username=None, subject=None, token=None):
        """Fetches a user token."""
        if username and subject and token:
            return cls.get_key(username, subject, token).get()

        assert subject and token, \
            'subject and token must be provided to UserToken.get().'
        return cls.query(cls.subject==subject, cls.token==token).get()