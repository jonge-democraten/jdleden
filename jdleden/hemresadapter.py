# coding=utf-8
# description: functions to interact with the newsletter subscriptions in jdwebsite (Hemres),
# via Hemres management commands

import os
import subprocess
import configparser
import logging

logger = logging.getLogger(__name__)


class HemresAdapter(object):

    def __init__(self):
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(scriptdir, 'ledenlijst.cfg')
        assert(os.path.exists(config_path))
        config = configparser.RawConfigParser()
        config.read(config_path)
        website_config = dict(config.items('jdwebsite'))
        self.python_bin_filepath = website_config['python_bin_filepath']  # this needs to be the python in the virtualenv of hemres
        assert(os.path.exists(self.python_bin_filepath))
        self.jdwebsite_manage_filepath = website_config['jdwebsite_manage_filepath']
        assert(os.path.exists(self.jdwebsite_manage_filepath))

    def subscribe_member_to_list(self, member_id, list_label):
        logger.debug('add_member_from_list(): member: ' + str(member_id) + ', list: ' + list_label)
        output = subprocess.check_output([self.python_bin_filepath, self.jdwebsite_manage_filepath, "janeus_subscribe", str(member_id), list_label])
        logger.debug('cout: ' + str(output))

    def unsubscribe_member_from_list(self, member_id, list_label):
        logger.debug('remove_member_from_list(): member: ' + str(member_id) + ', list: ' + list_label)
        output = subprocess.check_output([self.python_bin_filepath, self.jdwebsite_manage_filepath, "janeus_unsubscribe", str(member_id), list_label])
        logger.debug('cout: ' + str(output))

    def move_member(self, member_id, list_label_from, list_label_to):
        logger.debug('move_member()')
        self.unsubscribe_member_from_list(member_id, list_label_from)
        self.subscribe_member_to_list(member_id, list_label_to)


def test():
    hemres = HemresAdapter()
    hemres.subscribe_member_to_list(1, 'nieuwsbrief-utrecht')
    hemres.unsubscribe_member_from_list(1, 'nieuwsbrief-utrecht')
    hemres.subscribe_member_to_list(1, 'nieuwsbrief-amsterdam')
    hemres.move_member(1, 'nieuwsbrief-amsterdam', 'nieuwsbrief-utrecht')
    hemres.unsubscribe_member_from_list(1, 'nieuwsbrief-utrecht')

if __name__ == '__main__':
    print('main()')
    test()