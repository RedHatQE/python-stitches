import paramiko
import time


class Connection():
    '''
    Stateful object to represent paramiko connection to the host
    '''
    def __init__(self, instance, username="root", key_filename=None, timeout=10):
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
        self.cli.connect(hostname=self.private_hostname, username=username, key_filename=key_filename, look_for_keys=False, timeout=10)
        self.channel = self.cli.invoke_shell()
        self.sftp = self.cli.open_sftp()
        self.channel.setblocking(0)

    def reconnect(self):
        '''
        Close connection and open a new one
        '''
        self.cli.close()
        self.cli.connect(hostname=self.private_hostname, username=self.username, key_filename=self.key_filename)
        self.channel = self.cli.invoke_shell()
        self.sftp = self.cli.open_sftp()

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
	stdin, stdout, stderr = self.cli.exec_command(command)
	if stdout:
	    for i in range(timeout):
	        if stdout.channel.exit_status_ready():
		    return stdout.channel.recv_exit_status()
		time.sleep(1)
	else:
 	    return None	
