import logging

import ldap
import ldap.modlist as modlist

from jdleden import settings

logger = logging.getLogger(__name__)


class JDldap(object):
    def __init__(self):
        self.ldap_connection = None

    def connect(self):
        self.ldap_connection = ldap.initialize(settings.LDAP_NAME)
        try:
            self.ldap_connection.simple_bind_s(settings.LDAP_DN, settings.LDAP_PASSWORD)
        except ldap.LDAPError as e:
            logger.critical(str(e))
            raise

    def disconnect(self):
        if self.ldap_connection:
            self.ldap_connection.unbind_s()

    def doldap_remove(self, id):
        self.check_connection()
        dn_to_delete = "cn=" + str(int(id)) + ",ou=users,dc=jd,dc=nl"
        try:
            self.ldap_connection.delete_s(dn_to_delete)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not remove - " + str(int(id)))
            # raise # this can happen because the database is transactional but the LDAP not yet (script can come here twice)

    def doldap_add(self, lidnummer, naam, mail, afdeling):
        self.check_connection()
        dn_to_add = "cn=" + str(int(lidnummer)) + ",ou=users,dc=jd,dc=nl"
        attrs = {}
        attrs['objectclass'] = ['inetOrgPerson'.encode('utf8')]
        attrs['sn'] = naam.encode('utf8')
        attrs['mail'] = mail.encode('utf8')
        attrs['ou'] = afdeling.encode('utf8')

        ldif = modlist.addModlist(attrs)
        try:
            self.ldap_connection.add_s(dn_to_add, ldif)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not add - " + str(int(lidnummer)))
            # raise # this can happen because the database is transactional but the LDAP not yet (script can come here twice)

    def doldap_modify(self,lidnummer, naam, mail, afdeling):
        self.check_connection()
        dn_to_mod = "cn=" + str(int(lidnummer)) + ",ou=users,dc=jd,dc=nl"
        attrs = [(ldap.MOD_REPLACE, "sn", naam.encode('utf8')), (ldap.MOD_REPLACE, "mail", mail.encode('utf8')),
                 (ldap.MOD_REPLACE, "ou", afdeling.encode('utf8'))]
        try:
            self.ldap_connection.modify_s(dn_to_mod, attrs)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not modify - " + str(int(lidnummer)))
            raise

    def check_connection(self):
        if not self.ldap_connection:
            raise RuntimeError('No connection with LDAP!')