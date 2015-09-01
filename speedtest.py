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

import http.client
import time
from urllib.parse import urlparse

CHUNK_SIZE = 1024*512  # Size of a chunk to measure speed of.

class SpeedTest(object):
    def __init__(self, url):
        self.url = url
        self.scheme, self.host, self.path = self.parse(url)
        
        self.connection = self.create_connection()
        
    URL_SCHEMES = {
        'http': http.client.HTTPConnection,
        'https': http.client.HTTPSConnection,
    }

    @classmethod
    def parse(cls, url):
        """Parse a URI into a connection type, a host, and a file string.
        
        Arguments:
            url: A string containing the url, formatted to look like:
                https://example.com/some/filename/here.bin
        Returns:
            A tuple containing:
                The connection scheme class (e.g. http.client.HTTPConnection)
                The hostname (as a string)
                The path
        """
        parsed_url = urlparse(url)
        scheme = cls.URL_SCHEMES.get(parsed_url.scheme)
        if scheme is None:
            raise NotImplementedError(
                'Unimplemented or invalid URL scheme:', parsed_url.scheme)
        return (scheme, parsed_url.netloc, parsed_url.path)
        
    def create_connection(self):
        """Create a connection to the appropriate location.
        
        Returns: A connection object of the appropriate type.
        """
        return self.scheme(self.host)
    
    def connect(self):
        """Connect to the remote site.
        
        Returns:
            The time (in seconds) taken to establish the connection.
        """
        start_time = time.perf_counter()
        self.connection.connect()
        end_time = time.perf_counter()
        
        return end_time - start_time
    
    def get_speed(self):
        """Get the download speed.
        
        Returns: 
            The speed (in bytes per second) of the file download.
        """
        times = []
        self.connection.request('GET', self.path)
        self.response = self.connection.getresponse()
        while not self.response.isclosed():
            times.append(time.perf_counter())
            self.response.read(CHUNK_SIZE)
        speeds = []
        for i in range(1, len(times)):
            time_taken = times[i] - times[i-1]
            speeds.append(CHUNK_SIZE/time_taken)
        return speeds

def main():
    import statistics
    import sys
    test = SpeedTest(sys.argv[1])
    print('Time taken to connect: %.1f ms' % (test.connect() * 1000))
    speeds = test.get_speed()
    print('Average speed: %.2f kiB/s' % (statistics.mean(speeds)/1024))
    print('Average speed: %.2f Mbit/s' % (statistics.mean(speeds) * 8 / (10**6)))
    print('Max speed: %.2f kiB/s' % (max(speeds)/1024))
    print('Max speed: %.2f Mbit/s' % (max(speeds) * 8 / (10**6)))

if __name__ == '__main__':
    main()
