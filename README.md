# Web Service Clients Generator

`clientsgenerator.py` allows auto-generation of Sample CLI Clients for
[EMBL-EBI's Job Dispatcher Web Service Bioinformatics Tools](https://www.ebi.ac.uk/services).

## How to use it

Download the source code or clone the repository:

```bash
git clone https://github.com/ebi-jdispatcher/webservice-clients-generator.git
```

Specially if you have no root access to your machine, you might need to
use [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).
Prepare a virtual environment where all the Python dependencies will be installed.
This project has been developed and tested with Python 3.6.5.

```bash
virtualenv -p `which python` env
source ./env/bin/activate
# deactivate
```

A full list of Python dependencies is provided in [requirements.txt](requirements.txt). Install dependencies with:

```bash
pip install --upgrade -r requirements.txt
```

Now run the program to generate python clients for all supported EBI tools, they will be placed in the `dist` folder.
All available clients are listed in [clients.ini](clients.ini).

## Generating clients

Run the following commands to generate Python, Perl and Java clients for all the Bioinformatics tools provided.

```bash
# only python clients
python clientsgenerator.py python
```

```bash
# python, perl and java clients
python clientsgenerator.py python,perl,java
```

Alternatively, use `--client <client_name>` to get only a selected client.

```bash
python clientsgenerator.py python,perl,java --client clustalo
```

## Running the generated clients

### Python clients

The same `virtualenv` use to run the generator tool will have all the requirements to run the Python clients.
An example test for Clustal Omega Python client:

```bash
python dist/clustalo.py --email <your@email.com> --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

### Perl clients

In order to run Perl clients, Perl (tested version 5.22.0) needs to installed as well as two dependencies
(LWP and XML::Simple). Install these with:

```bash
# To install Perl dependencies run (you might need sudo)
cpan LWP
cpan XML::Simple
```

An example test for Clustal Omega Perl client:

```bash
perl dist/clustalo.pl --email <your@email.com> --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

### Java clients

In order to run Java clients, OpenJDK 8 (tested version 1.8.0_161") as well as ant (tested version 1.10.5), needs to installed. Note that OpenJDK 9 and above are not
currently supported. There are different build instructions for Windows and
Linux clients.

#### Windows

The Java source code needs to be compiled with `ant` as follows:
```bash
# if ant build fails on the first run, try the ant command line again
cd dist
ant -lib lib && rm -rf bin lib && cd -
```

An example test for Clustal Omega Java client:

```bash
java -jar dist/clustalo.jar --email <your@email.com> --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

#### Linux and OSX

The Java source code needs to be compiled:

```bash
cd dist && ./make_jars.sh
```

This creates JARS files which can be executed directly. An example test for Clustal Omega Java client:

```bash
dist/clustalo.jar --email <your@email.com> --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

The windows example above using java -jar will also work.

## Documentation

More documentation about [EMBL-EBI Bioinformatics Web Services](https://www.ebi.ac.uk/jdispatcher/docs/webservices/)

## Contact and Support

If you have any problems, suggestions or comments for our services please
contact us via [EBI Support](https://www.ebi.ac.uk/about/contact/support/job-dispatcher-services).

## License
The European Bioinformatics Institute - [EMBL-EBI](https://www.ebi.ac.uk/), is an Intergovernmental Organization which, as part of the European Molecular Biology Laboratory family, focuses on research and services in bioinformatics.  

Apache License 2.0. See [license](LICENSE) for details.
