#Installation
Configuring the neo4j url is done via the environment variable `NEO4J_BOLT_URL`.

When running for the first time make sure to run `neomodel_install_labels.py` to ensure all the 
constraints are set.

#Running
Run `insert.py` to insert the entire wordnet db into neo4j.