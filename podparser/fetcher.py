"""
The podfetcher is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

The podparser is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with the
podparser.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import os
import sys
import urllib2

import lxml.etree as ET

from parser import chdir

def fetch_pod():
    """
    Retrieve pod from remote URL and generate djvu xml files
    """

    arg_parser = argparse.ArgumentParser(
        description='Tool for fetcing postoffice directories')
    arg_parser.add_argument(
        '-d', '--directory',
        nargs=1,
        help='postoffice directory URL to be parsed')

    args = arg_parser.parse_args()

    if args.directory is None:
        print arg_parser.print_help()
        sys.exit(1)

    url = args.directory[0]
    istart = url.rfind('/') + 1
    if (istart) == len(url):
        istart = url.rfind('/', 0, istart -1) + 1
        iend = len(url) - 1
    else:
        iend = len(url)
        url = '{0}/'.format(url)

    if istart == 0:
        print "{0} isn't a valid URL".format(url)
        print arg_parser.print_help()
        sys.exit(1)

    pod_dir = url[istart: iend]
    fname = '{0}_meta.xml'.format(pod_dir)
    meta = '{0}{1}'.format(url, fname)

    # write metadata file
    print 'Fetching metadata ...'
    u = urllib2.urlopen(meta)
    f = open(fname, 'w')
    f.write(u.read())
    f.close()

    # write djvu file
    print 'Fetching djvu file ...'
    fname = '{0}_djvu.xml'.format(pod_dir)
    djvu = '{0}{1}'.format(url, fname)
    u = urllib2.urlopen(djvu)
    f = open(fname, 'w')
    f.write(u.read())
    f.close()

    print 'Generating page files ...'
    dir_name = fname.replace('.', '_')
    dom = ET.parse(fname)
    xslt = ET.parse('etc/DJVU.xsl')
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    with chdir(dir_name):
        transform = ET.XSLT(xslt)
        newdom = transform(dom)


if __name__ == "__main__":
    """
    Execute fetcher as command line process
    """
    fetch_pod()
