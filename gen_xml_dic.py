#
# mini-script to generate the pylatexenc._uni2latexmap_xml dict mapping
#
import sys

if sys.version_info.major > 2:
    # python 3
    unichr = chr

from xml.etree import ElementTree as ET

e = ET.parse('unicode.xml')

d = {}
dnames = {}

for chxml in e.find('charlist').iter('character'):
    Uid = chxml.attrib['id']
    if '-' in Uid:
        # composite/multiple characters not supported
        continue
    charord = int(Uid.lstrip('U'), 16)
    latexxml = chxml.find('latex')
    if latexxml is None:
        continue
    latexval = latexxml.text
    if latexval == unichr(charord):
        # "latex" representation is the same char directly
        continue
    if charord == 0x20:
        # skip space char
        continue
    if latexval.startswith(r'\ElsevierGlyph') or latexval.startswith(r'\El') \
       or latexval.startswith(r'\ensuremath{\El'):
        continue
    d[charord] = latexval
    dnames[charord] = chxml.find('description').text

# dump dictionary into module file
outputfile = 'pylatexenc/_uni2latexmap_xml.py'

HEADER = """\
# -*- coding: utf-8 -*-
#
# Automatically generated from unicode.xml by gen_xml_dic.py
#

"""

with open(outputfile, 'w') as f:
    f.write(HEADER)

    f.write("uni2latex = {\n")

    for k,v in d.items():
        f.write("0x%04X: %r,\n"%(k, v))

    f.write("}\n")

print("Successfully generated file %s"%(outputfile))


# Now see which characters we don't have in our default set of symbols
from pylatexenc._uni2latexmap import uni2latex as uni2latex_defaults

missing_keys = set(d.keys()).difference(set(uni2latex_defaults.keys()))
if missing_keys:
    print("#\n# Missing keys added from unicode.xml\n#\n")
    for k in sorted(missing_keys):
        if "'" not in d[k]:
            therepr = "r'"+d[k]+"'"
        else:
            therepr = repr(d[k])
        thedef = "0x%04X: %s,"%(k, therepr)
        print("%-50s# %s [%s]"%(thedef, dnames[k], unichr(k)))
    
