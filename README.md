# EBI Tools Generator
Tool to generate python clients for EBI's tools

### Overview

### How to use it

Clone the repository:

```git clone https://github.com/ebi-wp/ebi-tools-generator.git```

cd ebi-tools-generator

Install dependencies:

```pip install -r requirements.txt```

Just run the script and you obtain all the python clients for each EBI Tool

```$ python ebitoolsgenerator.py```

### Test the results

Run selected client. For example Clustal Omega:

```cd dist```

```python clustalo_universal.py --email afoix@ebi.ac.uk --sequence sp:wap_rat,sp:wap_mouse```

If you have no root access to your machine you might need to use virtualenv.

### Add a new tool

For add a new tool edit ```clients.ini``` and add the name tool and the category tool

### Documentation

More documnetation about the tools in [EBI Tools](https://www.ebi.ac.uk/seqdb/confluence/display/WEBSERVICES/EMBL-EBI+Web+Services)


