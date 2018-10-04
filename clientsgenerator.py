#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import textwrap
import requests
import subprocess
import configparser
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import easyargs


# Wrapper for a REST (HTTP GET) request
def restRequest(url):
    return requests.get(url).text


def escape(string):
    return " ".join(string.replace('\r\n', ' ').replace('\r', ' ').
                    replace('\n', ' ').replace('\t', ' ').strip().split())


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


def fetch_python_options(name, parameter):
    return ("parser.add_option('--%s', help=('%s'))"
            "" % (name, "'\n                  '".\
                  join(textwrap.wrap(escape(parameter[1]).strip(), width=70))))


def fetch_python_types(name, parameter):
    type = parameter[2]
    if type == u'BOOLEAN':
        return u'''\
    if options.{0}:
        params['{0}'] = True
    else:
        params['{0}'] = False'''.format(name)
    else:
        return u'''\
    if options.{0}:
        params['{0}'] = options.{0}'''.format(name)


def fetch_perl_options(name, parameter):
    if parameter[2] == u'BOOLEAN':
        return ("    '%s%s'%s=> \$params{'%s'},%s# %s" %
                (name, "", ((16 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter[1]).strip()))
    else:
        return ("    '%s%s'%s=> \$params{'%s'},%s# %s" %
                (name, ("=" + "%s" % parameter[2][0].lower()), ((14 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter[1]).strip()))


def fetch_perl_usage(name, parameter):
    if parameter[2] == u'BOOLEAN':
        return ("  --%s : %s : %s" %
                (name + (19 - len(name)) * " ", "bool" + (4 - len("bool")) * " ",
                 "\n                                 ".\
                    join(textwrap.wrap(escape(parameter[1]).strip(), width=70))))
    else:
        return ("  --%s : %s : %s" %
                (name + (19 - len(name)) * " ", "%s " %
                 (parameter[2][0:3].lower().replace("seq", "str").replace("dou", "int")),
                 "\n                                 ".\
                    join(textwrap.wrap(escape(parameter[1]).strip(), width=70))))


def fetch_perl_types(name):
    return u'''\
    if ($params{'%s'}) {
        $tool_params{'%s'} = 1;
    }
    else {
        $tool_params{'%s'} = 0;
    }''' % (name, name, name)


def generate_client(tool, template):
    return template.render(tool=tool)


def write_client(filename, contents, dir="dist"):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    with open(os.path.join(dir, filename), 'w') as fh:
        fh.write(contents)


@easyargs
def main(lang, client="all"):
    """Generates clients in 'Python', 'Perl' or 'Java'"""

    lang = lang.lower().split(",")
    if "python" in lang:
        # Python clients
        template = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'python', 'client.py.j2'))

        parser = configparser.ConfigParser()
        parser.read(u'clients.ini')
        for idtool in parser.keys():
            if client.lower() == "all" or client.lower() == idtool:
                if idtool == u'DEFAULT':
                    continue
                tool = {u'id': idtool,
                        u'url': u'http://www.ebi.ac.uk/Tools/services/rest/{}'.format(
                            idtool),
                        u'filename': u'{}.py'.format(idtool),
                        u'version': subprocess.check_output(
                            [u'git', u'describe', u'--always']).strip()
                            .decode('UTF-8'),
                        u'options': [],
                        u'types': []}

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options = []
                for (name, parameter) in parameters.items():
                    options.append(fetch_python_options(name, parameter))
                    tool[u'types'].append(fetch_python_types(name, parameter))

                tool[u'options'] = "\n".join(options)
                contents = generate_client(tool, template)

                write_client(tool[u'filename'], contents)
                print("Generating Python client for %s" % tool['url'])
    if "perl" in lang:
        # Perl clients
        template = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'perl', 'client.pl.j2'))

        parser = configparser.ConfigParser()
        parser.read(u'clients.ini')
        for idtool in parser.keys():
            if client.lower() == "all" or client.lower() == idtool:
                if idtool == u'DEFAULT':
                    continue
                tool = {u'id': idtool,
                        u'url': u'http://www.ebi.ac.uk/Tools/services/rest/{}'.format(
                            idtool),
                        u'filename': u'{}.pl'.format(idtool),
                        u'version': subprocess.check_output(
                            [u'git', u'describe', u'--always']).strip()
                            .decode('UTF-8'),
                        u'options': [],
                        u'usage': [],
                        u'checks': [],
                        }

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage, checks= [], [], []
                for (name, parameter) in parameters.items():
                    options.append(fetch_perl_options(name, parameter))
                    usage.append(fetch_perl_usage(name, parameter))
                    if parameter[2] == u'BOOLEAN':
                        checks.append(fetch_perl_types(name))

                tool[u'options'] = "\n".join(options)
                tool[u'usage'] = "\n".join(usage)
                tool[u'checks'] = "\n".join(checks)

                contents = generate_client(tool, template)

                write_client(tool[u'filename'], contents)
                print("Generating Perl client for %s" % tool['url'])
    if "java" in lang:
        print("%s not yet implemented" % lang)


if __name__ == u'__main__':
    main()
