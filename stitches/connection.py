"""
L{Connection}.
"""

import paramiko
import time
import subprocess
import os
import sys
import random
import string
import logging
import socket

class StitchesConnectionException(Exception):
    """ StitchesConnection Exception """
    pass

def lazyprop(func):
    """ Create lazy property """
    attr_name = '_lazy_' + func.__name__
    @property
    def _lazyprop(self):
        """ Create lazy property """
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    return _lazyprop


class Connection(object):
    """
    Stateful object to represent connection to the host
    """
    def __init__(self, instance, username="root", key_filename=None,
                 timeout=10, output_shell=False, disable_rpyc=False):
        """
        Create connection object

        @param instance: host parameters we would like to establish connection
                         to (or just a hostname)
        @type instance: dict or str

        @param username: user name for creating ssh connection
        @type username: str

        @param key_filename: file name with ssh private key
        @type key_filename: str

        @param timeout: timeout for creating ssh connection
        @type timeout: int

        @param output_shell: write output from this connection to standard
                             output
        @type output_shell: bool
        """
        self.logger = logging.getLogger('stitches.connection')

        if type(instance) == dict:
            self.parameters = instance.copy()
        else:
            self.parameters = {'private_hostname': instance,
                               'public_hostname': instance}
        # hostname is set for compatibility issues only, will be deprecated
        # in future
        if 'private_hostname' in self.parameters.keys() and \
                'public_hostname' in self.parameters.keys():
            # Custom stuff
            self.hostname = self.parameters['private_hostname']
            self.private_hostname = self.parameters['private_hostname']
            self.public_hostname = self.parameters['public_hostname']
        elif 'public_dns_name' in self.parameters.keys() and \
                'private_ip_address' in self.parameters.keys():
            # Amazon EC2/VPC instance
            if self.parameters['public_dns_name'] != '':
                # EC2
                self.hostname = self.parameters['public_dns_name']
                self.private_hostname = self.parameters['public_dns_name']
                self.public_hostname = self.parameters['public_dns_name']
            else:
                # VPC
                self.hostname = self.parameters['private_ip_address']
                self.private_hostname = self.parameters['private_ip_address']
                self.public_hostname = self.parameters['private_ip_address']
        if 'username' in self.parameters:
            self.username = self.parameters['username']
        else:
            self.username = username
        self.output_shell = output_shell
        if 'key_filename' in self.parameters:
            self.key_filename = self.parameters['key_filename']
        else:
            self.key_filename = key_filename
        self.disable_rpyc = disable_rpyc
        self.timeout = timeout

        # debugging buffers
        self.last_command = ""
        self.last_stdout = ""
        self.last_stderr = ""

        if self.key_filename:
            self.look_for_keys = False
        else:
            self.look_for_keys = True

        self.stdin_rpyc, self.stdout_rpyc, self.stderr_rpyc = None, None, None

        logging.getLogger("paramiko").setLevel(logging.WARNING)

    @lazyprop
    def cli(self):
        """ cli lazy property """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=self.private_hostname,
                       username=self.username,
                       key_filename=self.key_filename,
                       timeout=self.timeout,
                       look_for_keys=self.look_for_keys)
        # set keepalive
        transport = client.get_transport()
        transport.set_keepalive(3)
        return client

    @lazyprop
    def channel(self):
        """ channel lazy property """
        # start shell, non-blocking channel
        chan = self.cli.invoke_shell(width=360, height=80)
        chan.setblocking(0)
        # set channel timeout
        chan.settimeout(10)
        # now waiting for shell prompt ('username@')
        result = ""
        count = 0
        while count < 10:
            try:
                recv_part = chan.recv(16384).decode()
                result += recv_part
            except socket.timeout:
                # socket.timeout here means 'no more data'
                pass

            if result.find('%s@' % self.username) != -1:
                return chan
            time.sleep(1)
            count += 1
        # failed to get shell prompt on channel :-(
        raise StitchesConnectionException("Failed to get shell prompt")

    @lazyprop
    def sftp(self):
        """ sftp lazy property """
        return self.cli.open_sftp()

    @lazyprop
    def pbm(self):
        """ Plumbum lazy property """
        if not self.disable_rpyc:
            from plumbum import SshMachine
            return SshMachine(host=self.private_hostname, user=self.username,
                              keyfile=self.key_filename,
                              ssh_opts=["-o", "UserKnownHostsFile=/dev/null",
                                        "-o", "StrictHostKeyChecking=no"])
        else:
            return None

    @lazyprop
    def rpyc(self):
        """ RPyC lazy property """
        if not self.disable_rpyc:
            try:
                import rpyc

                devnull_fd = open("/dev/null", "w")
                rpyc_dirname = os.path.dirname(rpyc.__file__)
                rnd_id = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
                pid_filename = "/tmp/%s.pid" % rnd_id
                pid_dest_filename = "/tmp/%s%s.pid" % (rnd_id, rnd_id)
                rnd_filename = "/tmp/" + rnd_id + ".tar.gz"
                rnd_dest_filename = "/tmp/" + rnd_id + rnd_id + ".tar.gz"
                subprocess.check_call(["tar", "-cz", "--exclude", "*.pyc", "--exclude", "*.pyo", "--transform",
                                       "s,%s,%s," % (rpyc_dirname[1:][:-5], rnd_id), rpyc_dirname, "-f", rnd_filename],
                                      stdout=devnull_fd, stderr=devnull_fd)
                devnull_fd.close()

                self.sftp.put(rnd_filename, rnd_dest_filename)
                os.remove(rnd_filename)
                self.recv_exit_status("tar -zxvf %s -C /tmp" % rnd_dest_filename, 10)

                server_script = r"""
import os
print(os.environ)
from rpyc.utils.server import ThreadedServer
from rpyc import ClassicService
import sys
t = ThreadedServer(ClassicService, hostname = 'localhost', port = 0, reuse_addr = True)
fd = open('""" + pid_filename + r"""', 'w')
fd.write(str(t.port))
fd.close()
t.start()
"""
                if sys.version.startswith("3"):
                    python_ver = "python3"
                elif sys.version.startswith("2"):
                    python_ver = "python2"
                else:
                    python_ver = "python"

                ret = self.recv_exit_status(python_ver + " -V")
                if ret != 0:
                    self.logger.debug("%s not found on remote! ret:%s", python_ver, ret)
                    return None

                command = "echo \"%s\" | PYTHONPATH=\"/tmp/%s\" %s " % (server_script, rnd_id, python_ver)

                self.stdin_rpyc, self.stdout_rpyc, self.stderr_rpyc = self.exec_command(command, get_pty=True)
                self.recv_exit_status("while [ ! -f %s ]; do sleep 1; done" % (pid_filename), 10)
                self.sftp.get(pid_filename, pid_dest_filename)
                pid_fd = open(pid_dest_filename, 'r')
                port = int(pid_fd.read())
                pid_fd.close()
                os.remove(pid_dest_filename)

                return rpyc.classic.ssh_connect(self.pbm, port)

            except Exception as err:
                self.logger.debug("Failed to setup rpyc: %s" % err)
                return None
        else:
            return None

    def reconnect(self):
        """
        Close the connection and open a new one
        """
        self.disconnect()

    def disconnect(self):
        """
        Close the connection
        """
        if hasattr(self, '_lazy_sftp'):
            if self.sftp is not None:
                self.sftp.close()
            delattr(self, '_lazy_sftp')
        if hasattr(self, '_lazy_channel'):
            if self.channel is not None:
                self.channel.close()
            delattr(self, '_lazy_channel')
        if hasattr(self, '_lazy_cli'):
            if self.cli is not None:
                self.cli.close()
            delattr(self, '_lazy_cli')
        if hasattr(self, '_lazy_pbm'):
            if self.pbm is not None:
                self.pbm.close()
            delattr(self, '_lazy_pbm')
        if hasattr(self, '_lazy_rpyc'):
            if self.rpyc is not None:
                self.rpyc.close()
            delattr(self, '_lazy_rpyc')

    def exec_command(self, command, bufsize=-1, get_pty=False):
        """
        Execute a command in the connection

        @param command: command to execute
        @type command: str

        @param bufsize: buffer size
        @type bufsize: int

        @param get_pty: get pty
        @type get_pty: bool

        @return: the stdin, stdout, and stderr of the executing command
        @rtype: tuple(L{paramiko.ChannelFile}, L{paramiko.ChannelFile},
                      L{paramiko.ChannelFile})

        @raise SSHException: if the server fails to execute the command
        """
        self.last_command = command
        return self.cli.exec_command(command, bufsize, get_pty=get_pty)

    def recv_exit_status(self, command, timeout=10, get_pty=False):
        """
        Execute a command and get its return value

        @param command: command to execute
        @type command: str

        @param timeout: command execution timeout
        @type timeout: int

        @param get_pty: get pty
        @type get_pty: bool

        @return: the exit code of the process or None in case of timeout
        @rtype: int or None
        """
        status = None
        self.last_command = command
        stdin, stdout, stderr = self.cli.exec_command(command, get_pty=get_pty)
        if stdout and stderr and stdin:
            for _ in range(timeout):
                if stdout.channel.exit_status_ready():
                    status = stdout.channel.recv_exit_status()
                    self.last_stdout = stdout.read()
                    self.last_stderr = stderr.read()
                    break
                time.sleep(1)

            stdin.close()
            stdout.close()
            stderr.close()
        return status
