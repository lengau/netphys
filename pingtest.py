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
#

from ping import Ping
import statistics


class PingTest(object):
    """Ongoing statistics about ping requests to a variety of addresses."""

    def __init__(self, addresses, latest=False):
        """Create a PingTest object.

        Arguments:
            addresses: A list of strings containing the addresses to ping.
            latest: A boolean of whether to disregard older ping results.
        """
        self.addresses = list(addresses)
        self.__times = []
        self.__pings = []
        self.responses = []
        for address in addresses:
            ping = Ping(address)
            self.__pings.append(ping)
            self.__times.append(ping.ping(latest=latest))
            self.responses.append([])

    def __get_address_index(self, address):
        """Get the index of an address.

        Arguments:
            address: The address whose index to find. If address is an int or
                None, it is returned without modification.
        """
        if address is None or isinstance(address, int):
            return address
        return self.get(self.addresses.index(address))

    def get(self, address=None):
        """Get the next ping time to a specific address or all of them.

        Arguments:
            address: If address is None, returns a list of ping times for all
                addresses, in the same order as the addresses member.
                If address is an integer, return the ping time for that
                numbered address. If address is a string, look it up in
                addresses and return the ping time for it.
        """
        address = self.__get_address_index(address)
        if isinstance(address, int):
            response = self.__times[address].__next__()[1]
            self.responses[address].append(response)
            return response
        answer = []
        for index in range(len(self.__times)):
            answer.append(self.get(index))
        return answer

    def _do_stat(self, stat, address):
        """Run a function on one, or all addresses.

        Arguments:
            stat: The statistics function to run.
            address: Works as in get()
        """
        address = self.__get_address_index(address)
        if isinstance(address, int):
            return stat(self.responses[address])
        answers = []
        for index in range(len(self.__times)):
            answers.append(self._do_stat(stat, index))
        return answers

    def fastest(self, address=None):
        """Get the fastest response times for one or all addresses.

        Arguments:
            address: Works as in get.
        """
        return self._do_stat(min, address)

    def slowest(self, address=None):
        """Get the slowest response times for one or all addresses.

        Arguments:
            address: Works as in get.
        """
        return self._do_stat(max, address)

    def mean(self, address=None):
        """Get the average response time for one or all addresses.

        Arguments:
            address: Works as in get.
        """
        return self._do_stat(statistics.mean, address)

    def stop(self):
        """Stop all pings."""
        for ping in self.__pings:
            ping.stop()

    def remove(self, address):
        """Remove one ping.

        Arguments:
            address: Either the index or the address string to remove.
        """
        index = self.__get_address_index(address)
        self.addresses.pop(index)
        self.__times.pop(index)
        self.__pings[index].stop()
        self.__pings.pop(index)
        self.responses.pop(index)
