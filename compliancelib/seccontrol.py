#!/usr/bin/python
"""Class for 800-53 Security Controls

Instantiate class with Security Control ID (e.g., AT-2, CM-3).

Methods provide information about the Security Control.


This program is part of research for Homeland Open Security Technologies to better
understand how to map security controls to continuous monitoring.

Visit [tbd] for the latest version.
"""

__author__ = "Greg Elin (gregelin@govready.com)"
__version__ = "$Revision: 0.5 $"
__date__ = "$Date: 2015/10/11 18:02:00 $"
__copyright__ = "Copyright (c) 2015 GovReady PBC"
__license__ = "Apache Software License 2.0"

import os
import sys
import json
import yaml
import pprint
import commands
import re

# sys.path.append(os.path.join('xsl'))
# sys.path.append(os.path.join('data'))


class SecControl(object):
    "represent 800-53 security controls"
    def __init__(self, id):
        self.id = id
        if "(" in self.id:
            self._load_control_enhancement_from_xml()
        else:
            self._load_control_from_xml()
        # split description
        self.set_description_sections()
        
    def _load_control_from_xml(self):
        "load control detail from 800-53 xml"
        xslfile = os.path.join(os.path.dirname(__file__), 'xsl/control2json.xsl')
        xmlfile = os.path.join(os.path.dirname(__file__), 'data/800-53-controls.xml')
        # print xslfile
        # print "xsltproc --stringparam controlnumber '%s' %s %s" % (self.id, xslfile, xmlfile)
        results = commands.getstatusoutput("xsltproc --stringparam controlnumber '%s'  %s %s" % (self.id, xslfile, xmlfile))
        print results
        if (results[0] == 0) and (len(results[1]) > 0):
            self.details = json.loads(results[1])
            self.title = self.details["title"]
            self.description = self.details["description"]
            self.control_enhancements = self.details['control_enhancements']
            self.supplemental_guidance = self.details['supplemental_guidance']
            self.responsible = self._get_responsible()
        else:
            self.details = json.loads('{"id": null, "error": "Failed to get security control information from 800-53 xml"}')
            self.title = self.description = self.supplemental_guidance = self.control_enhancements = self.responsible = None
            self.details = {}

    def _load_control_enhancement_from_xml(self):
        "load control enhancement as a control from 800-53 xml"
        xslfile = os.path.join(os.path.dirname(__file__), 'xsl/controlenhancement2json.xsl')
        xmlfile = os.path.join(os.path.dirname(__file__), 'data/800-53-controls.xml')
        results = commands.getstatusoutput("xsltproc --stringparam controlnumber '%s' %s %s" % (self.id, xslfile, xmlfile))
        # print results
        if (results[0] == 0) and (len(results[1]) > 0):
            self.details = json.loads(results[1])
            self.title = self.details["title"]
            self.description = self.details["description"]
            self.control_enhancements = self.details['control_enhancements']
            self.supplemental_guidance = self.details['supplemental_guidance']
            self.responsible = self._get_responsible()
        else:
            self.details = json.loads('{"id": null, "error": "Failed to get security control information from 800-53 xml"}')
            self.title = self.description = self.supplemental_guidance = self.control_enhancements = self.responsible = None
            self.details = {}

    def _get_responsible(self):
        "determine responsibility"
        m = re.match(r'The organization|The information system|\[Withdrawn', self.description)
        if m:
            return {
                'The organization': 'organization',
                'The information system': 'information system',
                '[Withdrawn': 'withdrawn'
            }[m.group(0)]
        else:
            return "other"

    def get_control_json(self):
        "produce json version of control detail"
        self.json = {}
        self.json['id'] = self.id
        self.json['title'] = self.title
        self.json['description'] = self.description
        self.json['description_intro'] = self.description_intro
        self.json['description_sections'] = self.description_sections
        self.json['responsible'] = self.responsible
        self.json['supplemental_guidance'] = self.supplemental_guidance
        return self.json
        # To Do: needs test

    def get_control_yaml(self):
        "produce yaml version of control detail"
        sc_yaml = dict(
            id = self.id,
            title = self.title,
            description = self.description,
            description_intro = self.description_intro,
            description_sections = self.description_sections,
            responsible = self.responsible,
            supplemental_guidance = self.supplemental_guidance
        )
        return yaml.safe_dump(sc_yaml, default_flow_style=False)

    # utility functions
    def set_description_sections(self):
        """ splits a control description by lettered sub-sections """
        if self.description is None:
            self.description_intro = self.description_sections = None
            return True
        # temporarily merge sub-sectionsof sub-sections into sub-section, e.g., '\n\tAC-2h.1.'
        tmp_description = re.sub(r"\n\t[A-Z][A-Z]-[0-9]+[a-z]\.([0-9]+)\.", r" (\1)", self.description)
        # split subsections
        sections = re.compile("\n").split(tmp_description)
        self.description_intro = sections.pop(0)
        self.description_sections = sections
        return True

    def replace_line_breaks(self, text, break_src="\n", break_trg="<br />"):
        """ replace one type of line break with another in text block """
        if text is None:
            return ""
        if break_src in text:
            return break_trg.join(text.split(break_src))
        else:
            return text
