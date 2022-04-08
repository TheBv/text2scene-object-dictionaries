## Introduction
This is a project that's part of the practical Text2Scene course at the Goethe University in 
Frankfurt. More specifically this project initializes an object dictionary given the wordnet 
corpus. Optionally one can include similarity information from the FastText model as well as 
custom BERT relationships.

## Installation
Configuring the neo4j url is done via the environment variable `NEO4J_BOLT_URL`.

When running for the first time make sure to run `neomodel_install_labels.py` to ensure all the 
constraints are set.

## Running
### Insertion
Run `insert.py -a` to insert the entire wordnet db into neo4j.
Add `-wv` to also add the wordvector data.

To insert bert relations edit or create a new `relations` file given the template provided in 
`resources` make sure to add the newly added relationships to the `GraphModel.py` and Run 
`insert_bert_relations.py -file PATH`. You can make use of a gpu with `-gpu-device DEVICEID`

#### Dump
One can also grab the database dump from [here](https://github.com/TheBv/text2scene-object-dictionaries/releases/download/v0.1/neo4j.dump) and insert the database data that way

### Evaluation
To evaluate the predictive power of the default object dictionary one can run `evaluate.py` with 
the csv files provided 
in the resources. To generate their on csv files an example is provided below on how one could 
do so.

For `-relations` one can choose between `all-relations.csv`, `bert_relations.csv` and `no_bert.csv`
which contain all the relations, only the bert relations and all but the bert relations 
respectively.

For `-word-filter` one can choose between `root_object_words_numbers.csv` and 
`root_words_numbers.csv` which include only the object root words and all root words respectively.

With `-model-config` one can choose a different model configuration file. If none is specified 
it will default to `evaluation_params.json` in the root directory.
For reference on possible params look at [Ampligraph#evaluate_performance](https://docs.ampligraph.org/en/1.4.0/generated/ampligraph.evaluation.evaluate_performance.html)

Alternatively one can also define their own csv files to target specific relationships or words.

### Pre-run results
| ComplEx |  Wordnet-only | Bert-only | Combined |  FB15K*  | WN18* | WN18RR* |
|---|---|---|---|---|---|---|
| MRR | 0.7261 | 0.2826 | 0.8339 | 0.80 | 0.94 | 0.51|
| Hits@10 | 0.7481 | 0.3986 | 0.8589| 0.86  | 0.58 | 0.58 |
| Hits@1 | 0.7121 | 0.2197 | 0.8338 | 0.76  | 0.46 | 0.46 | 

<sub>* Values taken from</sub> [Ampligraph](https://docs.ampligraph.org/en/1.4.0/experiments.html)

The model configuration files for these results can be found in the resource folder

### Find optimal model

To find a possibly optimal model one can run `best_model.py`. The params that are considered to 
be used when trying to find an optimal model one can modify `best_model_params.py`.
For reference look at [Ampligraph#select_best_model_ranking](https://docs.ampligraph.org/en/1.4.0/generated/ampligraph.evaluation.select_best_model_ranking.html)

### Create custom csv files
**Prerequisite**: Make sure to install apoc to your neo4j database

The following example will create the `all_relations_numbers.csv` file which is provided 
automatically:
```cipher
WITH "Match path = (o:RootWord)-[r]->(k:RootWord) return id(o) as word1, type(r) as Relation, id(k) as word2" AS query
CALL apoc.export.csv.query(query, "all_relations_numbers.csv", {})
YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data;
```
For more details refer to: https://neo4j.com/labs/apoc/4.1/export/csv/
