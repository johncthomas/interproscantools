Turn a FASTA file of unknown sequences (like from a bacterial genome) into a table of
predicted functional domains.

IPRS sends sequences to a bunch of bioinformatic servers that predict the function
of the protein in various ways and combines those results.
https://www.ebi.ac.uk/interpro/about.html

These tools allow you to automate the uploading of sequences from a FastA file,
and produce an excel sheet summarising the results.

To install, make sure you have Python 3 and PIP
Then: pip install interproscantools-1.0.tar.gz

iprscan_from_fasta.py is used to send a series of amino acid sequences from a FastA file
to the InterProScan REST server. tabulate_iprs_results.py is used to produce a readable spreadsheet
file of IPRScan results. The results will consist of Gene Ontology terms, domain predictions,
and enzyme family predictions.

Works from the command line or imported as a module. For information on how to run from the
command line use:
    python iprscan_from_fasta.py -h
    python tabulate_iprs_results.py -h
Or from within python:
    from interproscantools.iprscan_from_fasta import iprscan
    from interproscantools.tabulate_iprs_results import make_excel_sheet
    print(iprscan.__doc__)
    print(make_excel_sheet.__doc__)
