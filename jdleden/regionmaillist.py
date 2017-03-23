import datetime
import logging

from jdleden.ledenlijst import read_xls, GEMEENTE, EMAIL

logger = logging.getLogger(__name__)


def create_region_mail_list(ledenlijst_input, gemeenten):
    gemeenten_lowercase = get_gemeenten_lowercase(gemeenten)
    members = read_xls(ledenlijst_input)
    emails = get_emails(members, gemeenten_lowercase)
    maillist_filepath = get_filename_output(gemeenten_lowercase)
    create_email_list(emails, maillist_filepath)
    return maillist_filepath, len(emails)


def get_emails(members, gemeenten_lowercase):
    emails = []
    for id in members:
        member = members[id]
        if member[GEMEENTE].lower() in gemeenten_lowercase:
            emails.append(member[EMAIL])
    return emails


def get_gemeenten_lowercase(gemeenten):
    gemeenten_lowercase_list = []
    for gemeente in gemeenten:
        gemeenten_lowercase_list.append(gemeente.lower())
    return gemeenten_lowercase_list


def get_filename_output(gemeenten):
    gemeenten_string = ''
    for gemeente in gemeenten:
        gemeenten_string += '_' + gemeente
    return str(datetime.date.today()) + gemeenten_string + '.txt'


def create_email_list(emails, filepath):
    with open(filepath, 'w') as fileout:
        for email in emails:
            if '@' in email:
                fileout.write(email + '\n')
