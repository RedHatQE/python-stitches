Stitches library
=================

Overview
--------
Stitches is a wrapper around Paramiko (https://github.com/paramiko/paramiko) and python-rpyc (http://rpyc.readthedocs.org/en/latest/).
It allows you to create connections to remote hosts and perform various shell/python actions on remote hosts. The library has 3 main 
parts: `Connection`, `Expect` and `Structure`

Connection
----------
`Connection` class represents connection to remote host.

Shell commands usage example:
      import stitches
      
      In [1]: con = stitches.connection.Connection('ec2host.eu-west-1.compute.amazonaws.com', key_filename='/home/user/.pem/eu-west-1-iam.pem', username='ec2-user')
      
      # Return value
      In [2]: con.recv_exit_status("ls -la /etc/passwd")
      Out[2]: 0

      In [3]: con.recv_exit_status("ls -la /non/existing/file")
      Out[3]: 2

      # Getting output
      In [4]: sin, sout, serr = con.exec_command("ls -la /etc/passwd /non/existing/file")

      In [5]: print sout.read()
      -rw-r--r--. 1 root root 1383 Sep  9 07:37 /etc/passwd

      In [6]: print serr.read()
      ls: cannot access /non/existing/file: No such file or directory

      # Timeout during command execution
      In [7]: print con.recv_exit_status("sleep 30", timeout=3)
      None

      # Some commands (e.g. sudo) require pty:
      In [1]: print con.recv_exit_status("sudo id", get_pty=True)
      0

RPyC example:
     # Built-in function open() on remote host
     In [1]: fd = con.rpyc.builtins.open('/etc/redhat-release')

     In [2]: print fd.read()
     Red Hat Enterprise Linux Server release 6.4 (Santiago)

     # Module on remote host
     In [3]: con.rpyc.modules.os.stat("/etc/passwd")
     Out[3]: posix.stat_result(st_mode=33188, st_ino=140905, st_dev=51777L, st_nlink=1, st_uid=0, st_gid=0, st_size=1383, st_atime=1382614681, st_mtime=1378726667, st_ctime=1378726667)
    
Expect
------
`Expect` class is being used for expect-like testing.
Example:

     # Expect sub-string in output
     In [1]: stitches.expect.Expect.ping_pong(con, "cat /etc/redhat-release", 'Red Hat')
     Out[1]: True

     # Failure will raise ExpectFailed exception:
     In [2]: stitches.expect.Expect.ping_pong(con, "cat /etc/redhat-release", 'Debian')
     ---------------------------------------------------------------------------
     ExpectFailed                              Traceback (most recent call last)
     ...
     ExpectFailed: cat /etc/redhat-release
     Red Hat Enterprise Linux Server release 6.4 (Santiago)
     [ec2-user@ip-10-234-98-44 ~]$
     
     # Matching
     In [3]: stitches.Expect.enter(con, 'cat /etc/redhat-release')
     Out[3]: 24

     In [4]: stitches.expect.Expect.match(con, re.compile('.*release ([0-9,\.]*).*', re.DOTALL))
     Out[4]: ['6.4']

     # Run a command and expect an exit status (0 by default)
     In [5]: stitches.expect.Expect.expect_retval(con "cat /etc/redhat-release /foo")
     ---------------------------------------------------------------------------
     ExpectFailed                              Traceback (most recent call last)
     ...
     stitches.expect.ExpectFailed: Got 1 exit status (0 expected)
     cmd: cat /etc/redhat-release /foo
     stdout: Red Hat Enterprise Linux release 8.0 Beta (Ootpa)

     stderr: cat: /foo: No such file or directory

Structure
---------
`Structure` class is being used to create whole testing setup with multiple hosts performing different roles. Structure is usually created based on YAML file:

Example YAML:
     Config: {param_a: a, param_b: b}
     Instances:
     - {private_hostname: hosta.compute.amazonaws.com, public_hostname: hosta.eu-west-1.compute.amazonaws.com,
       role: A_ROLE, username: ec2-user, key_filename: /home/user/.pem/eu-west-1-iam.pem}
     - {private_hostname: hostb.compute.amazonaws.com, public_hostname: hostb.eu-west-1.compute.amazonaws.com,
       role: B_ROLE, username: root, key_filename: /home/user/.pem/eu-west-1-iam.pem}

Usage example:
     In [1]: s = stitches.Structure()

     In [2]: s.setup_from_yamlfile('/tmp/str.yaml')
     
     # Now `Structure` object has connections to all instances, we can do whatever we want:

     In [3]: s.Instances['A_ROLE'][0].recv_exit_status('id')
     Out[3]: 0

     # And we have config as well:
     In [4]: s.config['param_a']
     Out[4]: 'a'

Dependencies
------------
Stitches needs some external dependencies:
* python-paramiko
* python-plumbum
* python-rpyc

python-paramiko version in Fedora-19 is OK, plumbum and rpyc should be at least:
* python-plumbum-1.1.0_gitebe4cc4-2.fc18.noarch
* python-rpyc-3.3.0git40daa0c6-2.fc18.noarch

Pre-built RPMs can be obtained here: https://rhuiqerpm.s3.amazonaws.com/index.html

Reporting issues
----------------
radek at redhat dot com

