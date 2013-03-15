"""
Class to represent the whole setup (a bunch of nodes)
"""


import logging
import yaml

from patchwork.connection import Connection


class Structure:
    """
    Stateful object to represent whole setup
    """
    def __init__(self):
        self.Instances = {}
        self.config = {}

    def __del__(self):
        """
        Close all connections
        """
        for role in self.Instances.keys():
            for connection in self.Instances[role]:
                connection.sftp.close()
                connection.cli.close()

    def reconnect_all(self):
        """
        Re-establish connection to all instances
        """
        for role in self.Instances.keys():
            for connection in self.Instances[role]:
                connection.reconnect()

    def addInstance(self,
                    role,
                    instance,
                    username='root',
                    key_filename=None,
                    output_shell=False):
        """
        Add instance to the setup

        @param role: instance's role
        @type role: str

        @param instance: host parameters we would like to establish connection
                         to
        @type instance: dict

        @param username: user name for creating ssh connection
        @type username: str

        @param key_filename: file name with ssh private key
        @type key_filename: str

        @param output_shell: write output from this connection to standard
                             output
        @type output_shell: bool
        """
        if not role in self.Instances.keys():
            self.Instances[role] = []
        logging.debug('Adding ' + role + ' with private_hostname ' +
                      instance['private_hostname'] +
                      ', public_hostname ' + instance['public_hostname'])
        self.Instances[role].append(Connection(instance,
                                               username,
                                               key_filename,
                                               output_shell=output_shell))

    def setup_from_yamlfile(self, yamlfile, output_shell=False):
        """
        Setup from yaml config

        @param yamlfile: path to yaml config file
        @type yamlfile: str

        @param output_shell: write output from this connection to standard
                             output
        @type output_shell: bool
        """
        logging.debug('Loading config from ' + yamlfile)
        fd = open(yamlfile, 'r')
        yamlconfig = yaml.load(fd)
        for instance in yamlconfig['Instances']:
            self.addInstance(instance['role'].upper(),
                             instance,
                             output_shell=output_shell)
        if 'Config' in yamlconfig.keys():
            logging.debug('Config found: ' + str(yamlconfig['Config']))
            self.config = yamlconfig['Config'].copy()
        fd.close()
