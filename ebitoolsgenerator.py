#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import requests
import subprocess
import configparser
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader


# Wrapper for a REST (HTTP GET) request
def restRequest(url):
    return requests.get(url).text


def escape(string):
    return string.replace('\'', '\\\'')\
        .replace('\n', '\\\n').replace('\t', '\\\t')


def tool_from(url):
    response = restRequest(url)
    description = escape(ET.fromstring(response).text)
    return description, parameters_of(url)


def parameters_of(url):
    response = restRequest(url + u'/parameters')
    params = ET.fromstring(response)
    return {param.text: details_of(url, param.text) for param in params}


def details_of(url, param_name):
    response = restRequest(url + u'/parameterdetails/' + param_name)
    details = ET.fromstring(response)
    return [detail.text for detail in details]


def fetch_option(name, parameter):
    param = dict()
    param[u'name'] = name
    param[u'help'] = escape(parameter[1])
    return param


def fetch_type(name, parameter):
    type = parameter[2]
    if type == u'BOOLEAN':
        return u'''    if options.{0}:
        params['{0}'] = True
    else:
        params['{0}'] = False'''.format(name)
    else:
        return u'''    if options.{0}:
            params['{0}'] = options.{0}'''.format(name)

def generate_client(tool, template):
    return template.render(tool=tool)


def write_client(name, filename, contents):
    dir = u'./dist'
    if not os.path.isdir(dir):
        os.mkdir(dir)
    with open(u'{}/{}_client.py'.format(dir, name), 'w') as fh:
        fh.write(contents)


if __name__ == u'__main__':
    template = Environment(loader=FileSystemLoader(u'.'))\
            .get_template(u'client.py.j2')

    parser = configparser.ConfigParser()
    parser.read(u'clients.ini')
    for idtool in parser.keys():
        if idtool == u'DEFAULT':
            continue
        tool = {u'id': idtool,
                u'url': u'http://www.ebi.ac.uk/Tools/services/rest/{}'.format(
                    idtool),
                u'filename': u'{}_client.py'.format(idtool),
                u'version': subprocess.check_output(
                    [u'git', u'describe', u'--always']).strip()
                .decode('UTF-8'),
                u'options': [],
                u'types': []}

        tool[u'description'], parameters = tool_from(tool[u'url'])

        for option in parser[idtool]:
            tool[option] = parser.get(idtool, option)

        for (name, parameter) in parameters.items():
            tool[u'options'].append(fetch_option(name, parameter))
            tool[u'types'].append(fetch_type(name, parameter))

        contents = generate_client(tool, template)

        write_client(tool[u'id'], tool[u'filename'], contents)
