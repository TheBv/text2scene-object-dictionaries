import os

import neomodel
from neomodel import (config, StructuredNode, StringProperty, ArrayProperty,
                      UniqueIdProperty, RelationshipTo)
config.DATABASE_URL = os.environ["NEO4J_BOLT_URL"]


class Word(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    definition = StringProperty()
    hypernyms = RelationshipTo('Word', 'HAS_HYPERNYM')
    hyponyms = RelationshipTo('Word', 'HAS_HYPONYM')
    member_holonyms = RelationshipTo('Word', 'HAS_HOLONYM')
    root_hypernyms = RelationshipTo('Word', 'HAS_ROOT_HYPERNYM')  # RelationshipFrom?
    # antonyms = RelationshipTo('Word', 'HAS_ANTONYM')
    # derivationally_related_forms = RelationshipTo('Word', 'HAS_HYPERNYM')
    lemmas = RelationshipTo('Lemma', "HAS_LEMMA")


class Lemma(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    antonyms = RelationshipTo('Lemma', 'HAS_ANTONYM')
    pertainyms = RelationshipTo('Lemma', 'HAS_PERTAINYMS')