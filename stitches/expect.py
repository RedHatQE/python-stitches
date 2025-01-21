"""
Expect-like stuff
"""

import re
import time
import logging
import socket
import sys

CTRL_C = '\x03'


class ExpectFailed(AssertionError):
    '''
    Exception to represent expectation error
    '''
    pass


class Expect(object):
    '''
    Stateless class to do expect-ike stuff over connections
    '''
    @staticmethod
    def expect_list(connection, regexp_list, timeout=10):
        '''
        Expect a list of expressions

        @param connection: Connection to the host
        @type connection: L{Connection}

        @param regexp_list: regular expressions and associated return values
        @type regexp_list: list of (regexp, return value)

        @param timeout: timeout for performing expect operation
        @type timeout: int

        @return: propper return value from regexp_list
        @rtype: return value

        @raises ExpectFailed
        '''
        result = ""
        count = 0
        while count < timeout:
            try:
                recv_part = connection.channel.recv(81920).decode()
                logging.getLogger('stitches.expect').debug("RCV: " + recv_part)
                if connection.output_shell:
                    sys.stdout.write(recv_part)
                result += recv_part
            except socket.timeout:
                # socket.timeout here means 'no more data'
                pass

            for (regexp, retvalue) in regexp_list:
                # search for the first matching regexp and return desired value
                if re.match(regexp, result):
                    return retvalue
            time.sleep(1)
            count += 1
        raise ExpectFailed(result)

    @staticmethod
    def expect(connection, strexp, timeout=10):
        '''
        Expect one expression

        @param connection: Connection to the host
        @type connection: L{Connection}

        @param strexp: string to convert to expression (.*string.*)
        @type strexp: str

        @param timeout: timeout for performing expect operation
        @type timeout: int

        @return: True if succeeded
        @rtype: bool

        @raises ExpectFailed
        '''
        return Expect.expect_list(connection,
                                  [(re.compile(".*" + strexp + ".*",
                                               re.DOTALL), True)],
                                  timeout)

    @staticmethod
    def match(connection, regexp, grouplist=[1], timeout=10):
        '''
        Match against an expression

        @param connection: Connection to the host
        @type connection: L{Connection}

        @param regexp: compiled regular expression
        @type regexp: L{SRE_Pattern}

        @param grouplist: list of groups to return
        @type group: list of int

        @param timeout: timeout for performing expect operation
        @type timeout: int

        @return: matched string
        @rtype: str

        @raises ExpectFailed
        '''
        logging.getLogger('stitches.expect').debug("MATCHING: " + regexp.pattern)
        result = ""
        count = 0
        while count < timeout:
            try:
                recv_part = connection.channel.recv(81920).decode()
                logging.getLogger('stitches.expect').debug("RCV: " + recv_part)
                if connection.output_shell:
                    sys.stdout.write(recv_part)
                result += recv_part
            except socket.timeout:
                # socket.timeout here means 'no more data'
                pass

            match = regexp.match(result)
            if match:
                ret_list = []
                for group in grouplist:
                    logging.getLogger('stitches.expect').debug("matched: " + match.group(group))
                    ret_list.append(match.group(group))
                return ret_list
            time.sleep(1)
            count += 1
        raise ExpectFailed(result)

    @staticmethod
    def enter(connection, command):
        '''
        Enter a command to the channel (with '\n' appended)

        @param connection: Connection to the host
        @type connection: L{Connection}

        @param command: command to execute
        @type command: str

        @return: number of bytes actually sent
        @rtype: int
        '''
        return connection.channel.send(command + "\n")

    @staticmethod
    def ping_pong(connection, command, strexp, timeout=10):
        '''
        Enter a command and wait for something to happen (enter + expect
        combined)

        @param connection: connection to the host
        @type connection: L{Connection}

        @param command: command to execute
        @type command: str

        @param strexp: string to convert to expression (.*string.*)
        @type strexp: str

        @param timeout: timeout for performing expect operation
        @type  timeout: int

        @return: True if succeeded
        @rtype: bool

        @raises ExpectFailed
        '''
        Expect.enter(connection, command)
        return Expect.expect(connection, strexp, timeout)

    @staticmethod
    def expect_retval(connection, command, expected_status=0, timeout=10):
        '''
        Run command and expect specified return valud

        @param connection: connection to the host
        @type connection: L{Connection}

        @param command: command to execute
        @type command: str

        @param expected_status: expected return value
        @type expected_status: int

        @param timeout: timeout for performing expect operation
        @type  timeout: int

        @return: return value
        @rtype: int

        @raises ExpectFailed
        '''
        retval = connection.recv_exit_status(command, timeout)
        if retval is None:
            raise ExpectFailed("Got timeout (%i seconds) while executing '%s'"
                               % (timeout, command))
        elif retval != expected_status:
            raise ExpectFailed("Got %s exit status (%s expected)\ncmd: %s\nstdout: %s\nstderr: %s"
                               % (retval, expected_status, connection.last_command,
                                  connection.last_stdout, connection.last_stderr))
        if connection.output_shell:
            sys.stdout.write("Run '%s', got %i return value\n"
                             % (command, retval))
        return retval
