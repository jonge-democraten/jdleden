
LDAP_NAME = 'ldap://'
LDAP_PASSWORD = ''
LDAP_DN = 'cn=writeuser,ou=sysUsers,dc=jd,dc=nl'

SECRET_KEY = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    }
}
