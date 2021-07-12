# Transition system miner implementation using Cypher queries
Python tool to run the Transition System Miner [[1]](#1) on graph event data in a Neo4j databse, through Cypher queries.
Includes list or set abstractions, horizon limit set by parameter <i>k</i>. This implementation is specifically for demonstration on (subsets of) the BPIC17 dataset.

## Usage
The tool requires a running Neo4j database, containing event data in the format proposed in [[2]](#2).
In ```gdb_ts_list_k_past.py```, set the neo4j URL, username and password to the appropriate values for the database.

The CLI option enables parameter entry at runtime, for one abstraction and value of k. Setting CLI to ```false``` results in running the miner for every combination of abstraction and _k_ as set in the ```abstrs``` and ```ks``` variables.

If the DOT option is set to ```true```, the dot output will be converted into three png files, one for each entity type.

To execute the algorithm, run ```gdb_ts_list_k_past.py```.

At runtime the user is asked to enter a subfolder name. All script outputs will be stored in subfolders ```{abstr}{k}/{subfolder_name}``` of the working directory.

## Output
The output consists of a .dot file containing the TS graph, as well as a text file containing the execution time to generate the transition system. If DOT is enabled, three .png files containing the connected components of the graph in the .dot output are generated.

## References
<a id="1">[1]</a>
Wil MP van der Aalst, Vladimir Rubin, Boudewijn F van Dongen,Ekkart Kindler, and Christian W Günther. 
Process mining: A two-step approach using transition systems and regions
.BPM Center ReportBPM-06-30, BPMcenter. org, 6, 2006.

<a id="2">[2]</a>
Stefan Esser and Dirk Fahland. 
Multi-dimensional event data in graph databases.
arXiv preprint arXiv:2005.14552, 2020.
