import jwt
from jwt import ExpiredSignatureError, PyJWTError

from rest_framework import authentication
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied

from carpool_be import settings


class IsAuthenticated(authentication.BaseAuthentication):
    def authenticate(self, request):
        if 'Authorization' not in request.headers:
            raise NotAuthenticated(detail='Authentication header missing')

        claims = self.get_claims(request.headers['Authorization'])

        if 'email' not in claims:
            raise NotFound(detail='User not found')

        data = {
            'user': claims['email']
        }

        request.auth_context = data
        return claims['email'], request.headers['Authorization'][7:]

    def authenticate_header(self, request):
        return 'Unauthorized'

    @classmethod
    def get_claims_from_token(cls, token, signing_key=None, algorithm=None):
        signing_key = signing_key if signing_key else settings.JWTConfig['SIGNING_KEY']
        algorithm = algorithm if algorithm else settings.JWTConfig['ALGORITHM']

        return jwt.decode(token, signing_key, algorithms=algorithm)

    @classmethod
    def get_claims(cls, token, signing_key=None, algorithm=None):
        try:
            claims_obj = cls.get_claims_from_token(token[7:], signing_key, algorithm)['claims']
        except ExpiredSignatureError as e:
            raise NotAuthenticated(detail='Token has expired')
        except PyJWTError as e:
            raise PermissionDenied(detail='Token not valid')
        except KeyError as e:
            raise PermissionDenied(detail='Claims not present')
        return claims_obj