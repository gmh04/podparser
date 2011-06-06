from xml.dom.minidom import getDOMImplementation

import argparse
import os
import re
import sys

arg_parser = argparse.ArgumentParser(description='Wrapper for Google geo-encoder')
arg_parser.add_argument('-f', '--file-name',
                        help='CSV file to parse',
                        required=True)
args = arg_parser.parse_args()
pod = args.file_name

cur_dir = os.path.dirname(sys.argv[0])
if len(cur_dir) == 0:
    cur_dir = '.'

os.chdir('%s%c..' % (cur_dir, os.sep))

podparser_dir = os.getcwd()
docs_dir      = '%s/docs' % podparser_dir
config_dir    = '%s/etc' % podparser_dir

csv = open('%s%c%s.csv' % (docs_dir,   os.sep, pod), 'r')
xml = open('%s%c%s.xml' % (config_dir, os.sep, pod), 'w')

impl        = getDOMImplementation()
doc         = impl.createDocument(None, "addresses", None)
top_element = doc.documentElement

for line in csv:
    csl = line.split(';')

    address = csl[0]
    first_part = csl[1]
    second_part = csl[2]
    area = csl[3]
    
    address = address[1: len(address) -1]

    anode = doc.createElement('address')
    top_element.appendChild(anode) 

    pnode = doc.createElement('pattern')
    anode.appendChild(pnode)
    pnode.appendChild(doc.createTextNode(address.lower()))

    snode = doc.createElement('street')
    anode.appendChild(snode)
    snode.appendChild(doc.createTextNode(address))

    area = area[1: len(area) -1]
    areas = area.split(',')

    areas_node = doc.createElement('areas')

    for a in areas:

        if len(a) == 0:
            continue

        area_node = doc.createElement('area') 
        areas_node.appendChild(area_node)

        name_node = doc.createElement('name') 
        area_node.appendChild(name_node)
        text = doc.createTextNode(a)
        name_node.appendChild(text)

    if areas_node.childNodes.length > 0:
        anode.appendChild(areas_node)

ugly_xml   = doc.toprettyxml(indent='  ')
text_re    = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)    
pretty_xml = text_re.sub('>\g<1></', ugly_xml)

xml.write(pretty_xml)

csv.close()
xml.close()
