#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import shutil
import textwrap
import requests
import subprocess
import configparser
from functools import reduce
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
            "" % (name, "'\n                  '". \
                  join(textwrap.wrap(escape(parameter[1]).strip().replace("'", ""), width=70))))


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
        return ("    '%s%s'%s=> \$tool_params{'%s'},%s# %s" %
                (name, "", ((16 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter[1]).strip()))
    else:
        return ("    '%s%s'%s=> \$tool_params{'%s'},%s# %s" %
                (name, ("=" + "%s" % parameter[2][0].lower().replace("c", "s").replace("d", "f")),
                 ((14 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter[1]).strip()))


def fetch_perl_usage(name, parameter):
    if parameter[2] == u'BOOLEAN':
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ". \
                 join(textwrap.wrap(escape(parameter[1]).strip(), width=60)))).rstrip(".") + "."
    else:
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ". \
                 join(textwrap.wrap(escape(parameter[1]).strip(), width=60)))).rstrip(".") + "."


def fetch_java_options(name, parameter):
    type = parameter[2]
    # for val in parameter
    if type == u'BOOLEAN':
        return ('        allOptions.addOption("%s", "", false, "%s");'
                '' % (name, '"\n                   + "'.
                      join(textwrap.wrap(escape(parameter[1]).strip().replace("'", ""), width=70))))
    else:
        return ('        allOptions.addOption("%s", "", true, "%s");'
                '' % (name, '"\n                   + "'.
                      join(textwrap.wrap(escape(parameter[1]).strip().replace("'", ""), width=70))))


def fetch_perl_types(name):
    return u'''\
    if ($params{'%s'}) {
        $tool_params{'%s'} = 1;
    }
    else {
        $tool_params{'%s'} = 0;
    }''' % (name, name, name)
def fetch_java_usage(name, parameter):
    return ('                                   + "  --%s %s\n'
            '' % (name + (19 - len(name)) * " ",
                  '\\n"\n                                   + "                        '.
                  join(textwrap.wrap(escape(parameter[1]).strip(), width=60)).rstrip('.\\n"') + '.\\n"'))


def fetch_java_clients(name):
    return u'''\
        <antcall target="jar-client">
            <param name="client" value="%s"/>
        </antcall>''' % name


def generate_client(tool, template):
    return template.render(tool=tool) + "\n"


def write_client(filename, contents, dir="dist"):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    with open(os.path.join(dir, filename), 'w') as fh:
        fh.write(contents)


def copy_java_build_contents(src, dest="dist"):
    dest = os.path.join(os.getcwd(), dest)
    os.makedirs(os.path.join(dest, "src", "restclient", "stubs"), exist_ok=True)
    files = []
    for (dirpath, dirnames, filenames) in os.walk(src):
        files += [reduce(os.path.join, os.path.join(dirpath, file).split(os.sep)[2:])
                  for file in filenames if not file.endswith(".j2")]
    for file in files:
        s = os.path.join(src, file)
        d = os.path.join(dest, file)
        if os.path.exists(d):
            os.remove(d)
        shutil.copy2(s, d)


@easyargs
def main(lang, client="all"):
    """Generates clients in 'Python', 'Perl' or 'Java'"""

    baseurl = "https://www.ebi.ac.uk/Tools/services/rest/"
    lang = lang.lower().split(",")
    client = client.lower().split(",")
    required_params = ["sequence", "asequence", "bsequence",
                       "email", "program", "stype", "database"]
    if "python" in lang:
        # Python clients
        template = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'python', 'client.py.j2'))

        parser = configparser.ConfigParser()
        parser.read(u'clients.ini')
        for idtool in parser.keys():
            if "all" in client or idtool in client:
                if idtool == u'DEFAULT':
                    continue
                tool = {u'id': idtool,
                        u'url': u'{}{}'.format(baseurl, idtool),
                        u'filename': u'{}.py'.format(idtool),
                        u'version': subprocess.check_output(
                            [u'git', u'describe', u'--always']).strip()
                            .decode('UTF-8'),
                        u'options': [],
                        u'usage': [],
                        u'types': []}

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage = [], []
                for (name, parameter) in parameters.items():
                    options.append(fetch_python_options(name, parameter))
                    tool[u'types'].append(fetch_python_types(name, parameter))
                    usage.append(fetch_perl_usage(name, parameter))

                tool[u'options'] = "\n".join(options)
                tool[u'usage'] = "\n".join(usage)
                contents = generate_client(tool, template)
                write_client(tool[u'filename'], contents)
                print("Generated Python client for %s" % tool['url'], flush=True)

    if "perl" in lang:
        # Perl clients
        template = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'perl', 'client.pl.j2'))

        parser = configparser.ConfigParser()
        parser.read(u'clients.ini')
        for idtool in parser.keys():
            if "all" in client or idtool in client:
                if idtool == u'DEFAULT':
                    continue
                tool = {u'id': idtool,
                        u'url': u'{}{}'.format(baseurl, idtool),
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

                options, usage, checks = [], [], []
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
                print("Generated Perl client for %s" % tool['url'], flush=True)

    if "java" in lang:
        # Java clients
        copy_java_build_contents(os.path.join('templates', 'java'))

        template_client = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'java', 'src',
                                       'restclient', 'RestClient.java.j2'))

        template_utils = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'java', 'src',
                                       'restclient', 'ClientUtils.java.j2'))

        template_xml = Environment(loader=FileSystemLoader(u'.')) \
            .get_template(os.path.join('templates', 'java', 'build.xml.j2'))

        buildxml = {"filename": u'build.xml'}
        clients, targets = [], []
        parser = configparser.ConfigParser()
        parser.read(u'clients.ini')
        for idtool in parser.keys():
            if "all" in client or idtool in client:
                if idtool == u'DEFAULT':
                    continue
                tool = {u'id': idtool,
                        u'hostname': u'www.ebi.ac.uk',
                        u'url': u'{}{}'.format(baseurl, idtool),
                        u'filename_client': os.path.join('src', 'restclient',
                                                         u'RestClient%s.java' % idtool),
                        u'filename_utils': os.path.join('src', 'restclient',
                                                        u'ClientUtils%s.java' % idtool),
                        u'options': [],
                        u'usage_req': [],
                        u'usage_opt': [],
                        u'usage': [],
                        }

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage_opt, usage_req = [], [], []
                for (name, parameter) in parameters.items():
                    options.append(fetch_java_options(name, parameter))
                    if name in required_params:
                        usage_req.append(fetch_java_usage(name, parameter))
                    else:
                        usage_opt.append(fetch_java_usage(name, parameter))

                tool[u'options'] = "\n".join(options)
                tool[u'usage_req'] = "\n".join(usage_req)
                tool[u'usage_opt'] = "\n".join(usage_opt)

                contents_client = generate_client(tool, template_client)
                contents_utils = generate_client(tool, template_utils)
                write_client(tool[u'filename_client'], contents_client)
                write_client(tool[u'filename_utils'], contents_utils)
                clients.append(fetch_java_clients(idtool))
                print("Generated Java client for %s" % tool['url'], flush=True)

        buildxml["clients"] = "\n".join(clients)
        contents_xml = generate_client(buildxml, template_xml)
        write_client(buildxml[u'filename'], contents_xml)


if __name__ == u'__main__':
    main()
