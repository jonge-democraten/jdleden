
DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.sqlite3",
        # DB name or path to database file if using sqlite3.
        "NAME": "dev.db",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

#################
# LDAP SETTINGS #
#################

LDAP_NAME = 'ldap://127.0.0.1:389/'
LDAP_DN = 'cn=writeall,ou=sysUsers,dc=jd,dc=nl'
LDAP_PASSWORD = ''

###################
# JANEUS SETTINGS #
###################

JANEUS_SERVER = "ldap://127.0.0.1:389/"
JANEUS_DN = "cn=readall,ou=sysUsers,dc=jd,dc=nl"
JANEUS_PASS = ""
