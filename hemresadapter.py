# coding=utf-8
# description: functions to interact with the newsletter subscriptions in jdwebsite (Hemres),
# via Hemres management commands

import os
import subprocess
import configparser

class HemresAdapter(object):

    def __init__(self):
        SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(SCRIPTDIR, 'ledenlijst.cfg')
        assert(os.path.exists(config_path))
        config = configparser.RawConfigParser()
        config.read(config_path)
        website_config = dict(config.items('jdwebsite'))
        self.python_bin_filepath = website_config['python_bin_filepath']
        assert(os.path.exists(self.python_bin_filepath))
        self.jdwebsite_manage_filepath = website_config['jdwebsite_manage_filepath']
        assert(os.path.exists(self.jdwebsite_manage_filepath))

    def add_member_to_list(self, member_id, list_label):
        print('add_member_from_list')
        subprocess.call([self.python_bin_filepath, self.jdwebsite_manage_filepath, "janeus_subscribe", str(member_id), list_label])

    def remove_member_from_list(self, member_id, list_label):
        print('remove_member_from_list')
        subprocess.call([self.python_bin_filepath, self.jdwebsite_manage_filepath, "janeus_unsubscribe", str(member_id), list_label])

    def move_member(self, member_id, list_label_from, list_label_to):
        print('move_member')
        self.remove_member_from_list(member_id, list_label_from)
        self.add_member_to_list(member_id, list_label_to)


def test():
    hemres = HemresAdapter()
    hemres.add_member_to_list(1, 'UTRECHT')
    hemres.remove_member_from_list(1, 'UTRECHT')
    hemres.move_member(1, 'AMSTERDAM', 'UTRECHT')

if __name__ == '__main__':
    print('main()')
    test();