#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import shutil
import datetime
import textwrap
import requests
import subprocess
import configparser
from functools import reduce
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import easyargs
import xmltodict


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
    values = {detail.tag: detail.text for detail in details}

    default_values = {'protein': [], 'nucleotide': [], 'vector': [], 'generic': []}
    if param_name != "stype":
        param = xmltodict.parse(response)
        for key, val in param['parameter'].items():
            if key == "values":
                if 'value' in param['parameter']['values']:
                    # loop over list of values
                    for value in param['parameter']['values']['value']:

                        # checks if key=context and key=defaultValueContexts exists
                        if 'properties' in value:
                            if 'property' in value['properties']:
                                # loop over list of properties
                                prop = value['properties']['property']
                                if type(prop) is list:
                                    for pro in prop:
                                        if 'key' in pro and 'value' in pro:
                                            if pro['key'] == 'defaultValueContexts' and 'value' in value:
                                                # all contexts == same as defaultValue
                                                for key in ["protein", "nucleotide", "vector"]:
                                                    if key in pro['value']:
                                                        default_values[key].append(value['value'])

                        # else try find generic 'defaultValue'
                        if 'defaultValue' in value and 'value' in value:
                            if value['defaultValue'] == 'true':
                                default_values['generic'].append(value['value'])
    values["default_values"] = default_values
    return values


def fetch_python_options(name, parameter):
    type = parameter["type"]
    # for val in parameter
    if type == u'BOOLEAN':
        return ("parser.add_option('--%s', action='store_true', help=('%s'))"
                "" % (name, "'\n                  '".
                      join(textwrap.wrap(escape(parameter["description"]).strip().replace("'", ""), width=70))))
    elif type == u'INTEGER':
        return ("parser.add_option('--%s', type=int, help=('%s'))"
                "" % (name, "'\n                  '".
                      join(textwrap.wrap(escape(parameter["description"]).strip().replace("'", ""), width=70))))
    else:
        return ("parser.add_option('--%s', type=str, help=('%s'))"
                "" % (name, "'\n                  '".
                      join(textwrap.wrap(escape(parameter["description"]).strip().replace("'", ""), width=70))))


def fetch_python_types(name, parameter):
    type = parameter["type"]
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


def fetch_python_usage(name, parameter):
    if parameter["type"] == u'BOOLEAN':
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ".
                 join(textwrap.wrap(escape(parameter["description"]).strip(), width=60)))).rstrip(".") + "."
    else:
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ".
                 join(textwrap.wrap(escape(parameter["description"]).strip(), width=60)))).rstrip(".") + "."


def get_python_default_values(name, parameter):
    string = ""
    if (parameter['default_values']['protein'] != [] and
            parameter['default_values']['nucleotide'] != [] and
            parameter['default_values']['vector'] != []):
        for key in ["protein", "nucleotide", "vector"]:
            if 'true' in parameter['default_values'][key] and 'false' in parameter['default_values'][key]:
                parameter['default_values'][key] = ['true']
            if parameter['default_values'][key] != [None]:
                def_val = ",".join(parameter['default_values'][key])
                if len(parameter['default_values'][key]) == 1:
                    if parameter["type"] == u'INTEGER':
                        string += ("    if options.stype == '%s':\n"
                                   "        if not options.%s:\n"
                                   "            params['%s'] = %s\n" % (key, name, name, def_val))
                    else:
                        string += ("    if options.stype == '%s':\n"
                                   "        if not options.%s:\n"
                                   "            params['%s'] = '%s'\n" % (key, name, name, def_val))
    elif parameter['default_values']['generic'] != []:
        if 'true' in parameter['default_values']['generic'] and 'false' in parameter['default_values']['generic']:
            parameter['default_values']['generic'] = ['true']
        if parameter['default_values']['generic'] != [None]:
            def_val = ",".join(parameter['default_values']['generic'])
            if len(parameter['default_values']['generic']) == 1:
                if parameter["type"] == u'INTEGER':
                    string += ("    if not options.%s:\n"
                               "        params['%s'] = %s\n"
                               "" % (name, name, def_val))
                else:
                    string += ("    if not options.%s:\n"
                               "        params['%s'] = '%s'\n"
                               "" % (name, name, def_val))

    if string == "" and parameter["type"] == u'BOOLEAN':
        string += """\
    if options.%s:
        params['%s'] = 'true'
    else:
        params['%s'] = 'false'
    \n""" % (name, name, name)

    string += """\
    if options.%s:
        params['%s'] = options.%s
    \n""" % (name, name, name)

    return string


def fetch_perl_options(name, parameter, database=False):
    if parameter["type"] == u'BOOLEAN':
        return ("    '%s%s'%s=> \$params{'%s'},%s# %s" %
                (name, "", ((16 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter["description"]).strip()))
    elif database:
        return ("    '%s%s'%s=> \@database,%s# %s" %
                (name, "=s", ((14 - len(name)) * " "),
                 ((25 - len(name)) * " "), escape(parameter["description"]).strip()))
    else:
        return ("    '%s%s'%s=> \$params{'%s'},%s# %s" %
                (name, ("=" + "%s" % parameter["type"][0].lower().replace("c", "s").replace("d", "f").replace("a", "s")),
                 ((14 - len(name)) * " "), name,
                 ((15 - len(name)) * " "), escape(parameter["description"]).strip()))


def fetch_perl_usage(name, parameter):
    if parameter["type"] == u'BOOLEAN':
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ".
                 join(textwrap.wrap(escape(parameter["description"]).strip(), width=60)))).rstrip(".") + "."
    else:
        return ("  --%s %s" %
                (name + (19 - len(name)) * " ",
                 "\n                        ".
                 join(textwrap.wrap(escape(parameter["description"]).strip(), width=60)))).rstrip(".") + "."


def get_perl_default_values(name, parameter):
    string = ""
    if (parameter['default_values']['protein'] != [] and
            parameter['default_values']['nucleotide'] != [] and
            parameter['default_values']['vector'] != []):
        for key in ["protein", "nucleotide", "vector"]:
            if 'true' in parameter['default_values'][key] and 'false' in parameter['default_values'][key]:
                parameter['default_values'][key] = ['true']
            if parameter['default_values'][key] != [None]:
                def_val = ",".join(parameter['default_values'][key])
                if len(parameter['default_values'][key]) == 1:
                    if parameter["type"] == u'INTEGER':
                        string += ("    if ($params{'stype'} eq '%s') {\n"
                                   "        if (!$params{'%s'}) {\n"
                                   "            $params{'%s'} = %s\n        }\n    }\n"
                                   % (key, name, name, def_val))
                    else:
                        string += ("    if ($params{'stype'} eq '%s') {\n"
                                   "        if (!$params{'%s'}) {\n"
                                   "            $params{'%s'} = '%s'\n        }\n    }\n"
                                   % (key, name, name, def_val))
    elif parameter['default_values']['generic'] != []:
        if 'true' in parameter['default_values']['generic'] and 'false' in parameter['default_values']['generic']:
            parameter['default_values']['generic'] = ['true']
        if parameter['default_values']['generic'] != [None]:
            def_val = ",".join(parameter['default_values']['generic'])
            if len(parameter['default_values']['generic']) == 1:
                if parameter["type"] == u'INTEGER':
                    string += ("    if (!$params{'%s'}) {\n"
                               "        $params{'%s'} = %s\n    }\n"
                               "" % (name, name, def_val))
                else:
                    string += ("    if (!$params{'%s'}) {\n"
                               "        $params{'%s'} = '%s'\n    }\n"
                               "" % (name, name, def_val))

    if string == "" and parameter["type"] == u'BOOLEAN':
        string += """\
    if ($params{'%s'}) {
        $params{'%s'} = 'true';
    }
    else {
        $params{'%s'} = 'false';
    }\n""" % (name, name, name)
    return string


def fetch_java_options(name, parameter):
    type = parameter["type"]
    # for val in parameter
    if type == u'BOOLEAN':
        return ('        allOptions.addOption("%s", "", false, "%s");'
                '' % (name, '"\n                   + "'.
                      join(textwrap.wrap(escape(parameter["description"]).strip().replace("'", ""), width=70))))
    else:
        return ('        allOptions.addOption("%s", "", true, "%s");'
                '' % (name, '"\n                   + "'.
                      join(textwrap.wrap(escape(parameter["description"]).strip().replace("'", ""), width=70))))


def fetch_java_usage(name, parameter):
    return ('                                   + "  --%s %s\n'
            '' % (name + (19 - len(name)) * " ",
                  '\\n"\n                                   + "                        '.
                  join(textwrap.wrap(escape(parameter["description"]).strip(), width=60)).rstrip('.\\n"') + '.\\n"'))


def fetch_java_clients(name):
    return u'''\
        <antcall target="jar-client">
            <param name="client" value="%s"/>
        </antcall>''' % name


def get_java_default_values(name, parameter):
    string = ""
    if (parameter['default_values']['protein'] != [] and
            parameter['default_values']['nucleotide'] != [] and
            parameter['default_values']['vector'] != []):
        for key in ["protein", "nucleotide", "vector"]:
            if 'true' in parameter['default_values'][key] and 'false' in parameter['default_values'][key]:
                parameter['default_values'][key] = ['true']
            if parameter['default_values'][key] != [None]:
                def_val = ",".join(parameter['default_values'][key])
                if len(parameter['default_values'][key]) == 1:
                    string += ('        if (cli.hasOption("stype") && cli.getOptionValue("stype") == "%s") {\n'
                               '            if (cli.hasOption("%s") == false) {\n'
                               '                form.putSingle("%s", "%s");\n'
                               '            }\n        }\n' % (key, name, name, def_val))

    elif parameter['default_values']['generic'] != []:
        if 'true' in parameter['default_values']['generic'] and 'false' in parameter['default_values']['generic']:
            parameter['default_values']['generic'] = ['true']
        if parameter['default_values']['generic'] != [None]:
            def_val = ",".join(parameter['default_values']['generic'])
            if len(parameter['default_values']['generic']) == 1:
                string += ('        if (cli.hasOption("%s") == false)\n'
                           '           form.putSingle("%s", "%s");\n'
                           '' % (name, name, def_val))

    if string == "" and parameter["type"] == u'BOOLEAN':
        string += """\
        if (cli.hasOption("%s") == true) {
            form.putSingle("%s", "true");
        } else {
            form.putSingle("%s", "false");
        }\n""" % (name, name, name)
    return string


def generate_client(tool, template):
    return template.render(tool=tool) + "\n"


def write_client(filename, contents, dir="dist"):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    with open(os.path.join(dir, filename), 'w') as fh:
        if sys.version_info.major < 3:
            fh.write(contents.encode('ascii', 'ignore').decode('ascii'))
        else:
            fh.write(contents.encode('utf-8', 'ignore').decode('utf-8'))


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
def main(lang, client="all",
         baseurl="https://www.ebi.ac.uk/Tools/services/rest/"):
    """Generates clients in 'Python', 'Perl' or 'Java'"""

    lang = lang.lower().split(",")
    client = client.lower().split(",")
    required_params = ["sequence", "asequence", "bsequence",
                       "email", "program", "stype", "database"]
    datetimenow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                        u'usage_req': [],
                        u'usage_opt': [],
                        u'types': [],
                        u'default_values': [],
                        u'client_version': datetimenow,
                        }

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage_opt, usage_req, def_values = [], [], [], []

                for (name, parameter) in parameters.items():
                    options.append(fetch_python_options(name, parameter))
                    if name in required_params:
                        usage_req.append(fetch_python_usage(name, parameter))
                        if "sequence" not in name:
                            tool[u'types'].append(fetch_python_types(name, parameter))
                    else:
                        usage_opt.append(fetch_python_usage(name, parameter))
                        values = get_python_default_values(name, parameter)
                        if values != "":
                            def_values.append(values)

                tool[u'options'] = "\n".join(options)
                tool[u'usage_req'] = "\n".join(usage_req)
                tool[u'usage_opt'] = "\n".join(usage_opt)
                tool[u'default_values'] = "\n".join(def_values)
                contents = generate_client(tool, template)
                write_client(tool[u'filename'], contents)
                print("Generated Python client for %s" % tool['url'])

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
                        u'usage_req': [],
                        u'usage_opt': [],
                        u'default_values': [],
                        u'client_version': datetimenow,
                        }

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage_opt, usage_req, types, def_values = [], [], [], [], []
                for (name, parameter) in parameters.items():
                    options.append(fetch_perl_options(name, parameter,
                                                      database=True if name == "database" else False))
                    if name in required_params:
                        usage_req.append(fetch_perl_usage(name, parameter))
                    else:
                        usage_opt.append(fetch_perl_usage(name, parameter))
                        values = get_perl_default_values(name, parameter)
                        if values != "":
                            def_values.append(values)

                tool[u'options'] = "\n".join(options)
                tool[u'usage_req'] = "\n".join(usage_req)
                tool[u'usage_opt'] = "\n".join(usage_opt)
                tool[u'default_values'] = "\n".join(def_values)
                contents = generate_client(tool, template)
                write_client(tool[u'filename'], contents)
                print("Generated Perl client for %s" % tool['url'])

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
                        u'default_values': [],
                        u'client_version': datetimenow,
                        }

                tool[u'description'], parameters = tool_from(tool[u'url'])

                for option in parser[idtool]:
                    tool[option] = parser.get(idtool, option)

                options, usage_opt, usage_req, def_values = [], [], [], []
                for (name, parameter) in parameters.items():
                    options.append(fetch_java_options(name, parameter))
                    if name in required_params:
                        usage_req.append(fetch_java_usage(name, parameter))
                    else:
                        usage_opt.append(fetch_java_usage(name, parameter))
                        values = get_java_default_values(name, parameter)
                        if values != "":
                            def_values.append(values)

                tool[u'options'] = "\n".join(options)
                tool[u'usage_req'] = "\n".join(usage_req)
                tool[u'usage_opt'] = "\n".join(usage_opt)
                tool[u'default_values'] = "\n".join(def_values)
                contents_client = generate_client(tool, template_client)
                contents_utils = generate_client(tool, template_utils)
                write_client(tool[u'filename_client'], contents_client)
                write_client(tool[u'filename_utils'], contents_utils)
                clients.append(fetch_java_clients(idtool))
                print("Generated Java client for %s" % tool['url'])

        buildxml["clients"] = "\n".join(clients)
        contents_xml = generate_client(buildxml, template_xml)
        write_client(buildxml[u'filename'], contents_xml)


if __name__ == u'__main__':
    main()
