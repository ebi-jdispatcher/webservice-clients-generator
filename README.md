# EBI Tools Generator
Tool to generate python clients for EBI's tools

### How to use it

Clone the repository:

```bash
git clone https://github.com/ebi-wp/ebi-tools-generator.git
cd ebi-tools-generator
```

Install dependencies:

```bash
pip install -r requeriments.txt
```

Now run the program to generate python clients for all supported EBI tools, they will be placed in the `dist` folder

```bash
python ebitoolsgenerator.py
```

### External dependencies
To run the clients you need to install:

```bash
pip install xmltramp2
```

### Test the results

Run selected client. For example Clustal Omega:

```bash
cd dist
python clustalo_client.py --email support@ebi.ac.uk --sequence sp:wap_rat,sp:wap_mouse,sp:wap_pig
```

If you have no root access to your machine you might need to use [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

### Add a new tool

To add a new tool edit `clients.ini` , add the name tool and the category tool.

### Documentation

More documentation about the tools in [EBI Tools](https://www.ebi.ac.uk/seqdb/confluence/display/WEBSERVICES/EMBL-EBI+Web+Services)
