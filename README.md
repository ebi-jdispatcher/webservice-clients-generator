# Web Service Clients Generator

`clientsgenerator.py` allows auto-generation of Sample CLI Clients for 
[EMBL-EBI's Job Dispatcher Web Service Bioinformatics Tools](https://www.ebi.ac.uk/services).

## How to use it

Download the source code or clone the repository:

```bash
git clone https://github.com/ebi-wp/webservice-clients-generator.git
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

Run the following command to generate Python for all the Bioinformatics tools provided. 

```bash
python clientsgenerator.py python
```

Alternatively, use `--client <client_name>` to get only a selected client. 

```bash
python clientsgenerator.py python --client clustalo
```

## Running the generated clients

### Python clients

The same `virtualenv` use to run the generator tool will have all the requirements to run the Python clients.

## Test the results

An example test for Clustal Omega Python client:

```bash
python dist/clustalo.py --email <your@email.com> --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

## Documentation

More documentation about [EMBL-EBI Bioinformatics Web Services](https://www.ebi.ac.uk/seqdb/confluence/display/WEBSERVICES/EMBL-EBI+Web+Services)


## Contact and Support

If you have any problems, suggestions or comments for our services please
contact us via [EBI Support](http://www.ebi.ac.uk/support/index.php?query=WebServices).
