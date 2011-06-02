from xml.dom.minidom import getDOMImplementation

import os
import re
import sys

cur_dir = os.path.dirname(sys.argv[0])
if len(cur_dir) == 0:
    cur_dir = '.'

os.chdir('%s%c..' % (cur_dir, os.sep))

podparser_dir = os.getcwd()
docs_dir      = '%s/docs' % podparser_dir
config_dir    = '%s/etc' % podparser_dir

# just change this
pod = 'glasgow-1881-82'

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

    for a in areas:

        if len(a) == 0:
            continue

        areas_node = doc.createElement('areas')
        anode.appendChild(areas_node)

        area_node = doc.createElement('area') 
        areas_node.appendChild(area_node)
        text = doc.createTextNode(a)
        area_node.appendChild(text)

ugly_xml   = doc.toprettyxml(indent='  ')
text_re    = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)    
pretty_xml = text_re.sub('>\g<1></', ugly_xml)

xml.write(pretty_xml)

csv.close()
xml.close()
