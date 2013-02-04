import paramiko
import time


class Connection():
    '''
    Stateful object to represent paramiko connection to the host
    '''
    def __init__(self, instance, username="root", key_filename=None, timeout=10, output_shell=False):
        self.parameters = instance.copy()
        # hostname is set for compatibility issues only, will be deprecated in future
        if 'private_hostname' in instance.keys() and 'public_hostname' in instance.keys():
            # Custom stuff
            self.hostname = instance['private_hostname']
            self.private_hostname = instance['private_hostname']
            self.public_hostname = instance['public_hostname']
        elif 'public_dns_name' in instance.keys() and 'private_ip_address' in instance.keys():
            # Amazon EC2/VPC instance
            if instance['public_dns_name'] != '':
                # EC2
                self.hostname = instance['public_dns_name']
                self.private_hostname = instance['public_dns_name']
                self.public_hostname = instance['public_dns_name']
            else:
                # VPC
                self.hostname = instance['private_ip_address']
                self.private_hostname = instance['private_ip_address']
                self.public_hostname = instance['private_ip_address']
        self.username = username
        self.key_filename = key_filename
        self.cli = paramiko.SSHClient()
        self.cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_filename:
            look_for_keys = False
        else:
            look_for_keys = True
        self.cli.connect(hostname=self.private_hostname, username=username, key_filename=key_filename, look_for_keys=look_for_keys, timeout=10)
        self.channel = self.cli.invoke_shell(width=360, height=80)
        self.sftp = self.cli.open_sftp()
        self.channel.setblocking(0)
        self.output_shell = output_shell

    def reconnect(self):
        '''
        Close connection and open a new one
        '''
        self.cli.close()
        self.cli.connect(hostname=self.private_hostname, username=self.username, key_filename=self.key_filename)
        self.channel = self.cli.invoke_shell(width=360, height=80)
        self.sftp = self.cli.open_sftp()
        self.channel.setblocking(0)

    def exec_command(self, command, bufsize=-1):
        '''
        execute a command in the connection
        @param command:  a string command to execute
        @param bufsize:  paramiko bufsize option
        @return (stdin, stdout, stderr)
        '''
        return self.cli.exec_command(command, bufsize)

    def recv_exit_status(self, command, timeout):
	'''
	Get result from executed command
	@param command:  a string command to execute
	@param timeout: timeout
	'''
        status = None
	stdin, stdout, stderr = self.cli.exec_command(command)
	if stdout and stderr and stdin:
	    for i in range(timeout):
	        if stdout.channel.exit_status_ready():
                    status = stdout.channel.recv_exit_status()
                    break
		time.sleep(1)
            stdin.close()
            stdout.close()
            stderr.close()
        return status
