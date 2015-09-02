#
# Copyright (c) 2015 Alex Lowe <amlowe@ieee.org>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# TODO: Windows support?

"""
To anyone considering using this module: please consider using the
[ping module](https://pypi.python.org/pypi/ping) on PyPI instead.

I wrote this because the ping module requires root access, and I want netphys
to run as a standard user.

If you happen to need the same and want to use this module, please contact me.
I'll be happy to help move it into its own package and make the necessary
changes to allow other software to use it.
"""

import ipaddress
import itertools
import logging
import platform
import random
import socket
import subprocess

logging.basicConfig(level=logging.DEBUG)


class FindAddressError(Exception):
    """Cannot find an address.

    Raised if we cannot get an appropriate IP address from a host passed into
    the Ping constructor. Often caused by an IPv4-only host being used with
    ipv6=true.
    """
    pass


class Ping(object):
    """An object that can ping a host.

    This is a wrapper around the operating system's ping command. It was
    written as an alternative to using a pure-Python ping implementation since
    that would require root access. (On most OS's ping is setuid root, which
    circumvents the need for root access by this module.)
    """

    def __init__(self, host, ipv6=None, adaptive=True, timestamp=False):
        """Create a Ping object, ready to ping one or more hosts.

        Arguments:
            host: Either a hostname (e.g. example.org) or an IP address
                  of a host. Any address that can be used in socket.getaddrinfo
                  may be used here.
            ipv6: A boolean (or None) of whether to use IPv6. Forces IPv6 use
                  if true or IPv4 if False. If None, it uses the first type
                  of address returned by socket.getaddrinfo().
                  If set to True or False, creating a Ping object will raise
                  an error if the host specified doesn't have an appropriate
                  record (or the wrong type of IP address is specified).
            Other arguments correspond directly to arguments in ping. The
            argument is not added if the variable is None.
                adaptive: -A
                timestamp: -D

            TODO: Allow the addition of arbitrary arguments.
        """
        if ipv6 is True:
            address_family = socket.AddressFamily.AF_INET6
        elif ipv6 is False:
            address_family = socket.AddressFamily.AF_INET
        else:
            address_family = 0  # Any type of address.

        try:
            self.host = socket.getaddrinfo(
                host, 0, family=address_family)[0][4][0]
        except socket.gaierror as e:
            raise FindAddressError from e

        self.adaptive = adaptive
        self.timestamp = timestamp
        self.ipv6 = isinstance(
            ipaddress.ip_address(self.host), ipaddress.IPv6Address)

    def __run_ping(self, count):
        """Run the ping command as a subprocess.

        This is here as an abstraction layer for later compatibility with
        multiple ping commands. For the moment, it works nicely with the ping
        utility in Debian/Ubuntu's iputils-ping, raises a NotImplementedError
        if run on Windows due to a different implementation of ping, and has
        unknown (but assumed good) behaviour on other platforms.

        Arguments:
            count: The number of packets to send.
        Returns:
            A subprocess.Popen object linked to the process.
        """
        if platform.system() == 'Windows':
            raise NotImplementedError(
                'Windows support has not yet been implemented.')

        if self.ipv6:
            args = ['ping6']
        else:
            args = ['ping']
        if self.adaptive is True:
            args.append('-A')
        if count is not None:
            args.extend(['-c', str(count)])
        if self.timestamp is True:
            args.append('-D')

        args.append(self.host)
        return subprocess.Popen(args, stdout=subprocess.PIPE)

    def ping(self, packets=None, latest=False):
        """Generate ping statistics.

        Arguments:
            packets: How many packets to send.
            latest: If this is True and packets is None, ping will always
                yield the most recent packet, regardless of how many packets
                have been received since the last yield.
                This has no effect if the number of packets is limited.

        Yields:
            A double of the ICMP sequence and the round trip time.
        """
        self.ping_command = self.__run_ping(packets)
        self.ping_command.stdout.readline()
        if packets is None:
            counter = itertools.count()
        else:
            counter = range(packets)
        for _ in counter:
            if packets is None and latest:
                line = self.ping_command.stdout.readline().split()
                while self.ping_command.stdout.peek().count(b'\n') > 1:
                    line = self.ping_command.stdout.readline().split()
            else:
                line = self.ping_command.stdout.readline().split()
            icmp_seq = int(find_starting_item(line, b'icmp_seq=')[9:])
            if 'Unreachable' in line:
                time = None
            else:
                time = find_starting_item(line, b'time=')[5:]
                # Just in case there's no space between the time and the units:
                while not bytes.isdigit(time[-1:]):
                    time = time[:-1]
                time = float(time)
            yield (icmp_seq, time)
        raise StopIteration()

    def stop(self):
        """Stop an ongoing ping process."""
        try:
            self.ping_command.kill()
        except AttributeError:
            pass

    def __del__(self):
        self.stop()


def find_starting_item(iterable, search_term):
    """Find the object starting with search_term in iterable.

    The type of the search term must match the type of the object
    being searched for, and the object being searched for must implement
    the startswith() method.

    Arguments:
        iterable: The item to search in. Normally a list or tuple.
        search_term: The starting item to search for.

    Returns:
        The first object matching that matches search_term, or None if
        no item is found.

    TODO: Move this into a generic library.
    """
    for item in iterable:
        if type(item) != type(search_term):
            continue
        if item.startswith(search_term):
            return item


def main():
    import sys
    ping = Ping(sys.argv[1])
    print('Pinging address:', ping.host)
    try:
        for result in ping.ping():
            print(result)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
