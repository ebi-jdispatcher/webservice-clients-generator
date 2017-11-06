# EBI Tools Generator
Tool to generate python clients for EBI's tools

### How to use it

Clone the repository:

```git clone https://github.com/ebi-wp/ebi-tools-generator.git```

```cd ebi-tools-generator```

Install dependencies:

```pip install -r requirements.txt```

Now run the program to generate python clients for all supported EBI tools, they will be placed in the `dist` folder

```python ebitoolsgenerator.py```

### Test the results

Run selected client. For example Clustal Omega:

```cd dist```

```python clustalo_universal.py --email afoix@ebi.ac.uk --sequence sp:wap_rat,sp:wap_mouse```

If you have no root access to your machine you might need to use virtualenv.

### Add a new tool

To add a new tool edit ```clients.ini``` , add the name tool and the category tool

### Documentation

More documnetation about the tools in [EBI Tools](https://www.ebi.ac.uk/seqdb/confluence/display/WEBSERVICES/EMBL-EBI+Web+Services)


