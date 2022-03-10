import os

from neomodel import (config, StructuredNode, StringProperty, RelationshipTo, DoesNotExist,
                      StructuredRel, FloatProperty)
from neomodel.properties import AliasProperty,Property
from neomodel.relationship_manager import RelationshipDefinition
config.DATABASE_URL = os.environ["NEO4J_BOLT_URL"]


class Synset(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    definition = StringProperty()
    hypernyms = RelationshipTo('Synset', 'HAS_HYPERNYM')
    hyponyms = RelationshipTo('Synset', 'HAS_HYPONYM')
    member_holonyms = RelationshipTo('Synset', 'HAS_HOLONYM')
    root_hypernyms = RelationshipTo('Synset', 'HAS_ROOT_HYPERNYM')
    lemmas = RelationshipTo('Lemma', "HAS_LEMMA")


class SubsetRel(StructuredRel):
    weight = FloatProperty()


class Lemma(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    antonyms = RelationshipTo('Lemma', 'HAS_ANTONYM')
    pertainyms = RelationshipTo('Lemma', 'HAS_PERTAINYMS')
    root_word = RelationshipTo('RootWord', 'SUBSET_OF')


class RootWord(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    contains = RelationshipTo('Lemma', "CONTAINS")
    similar = RelationshipTo('RootWord', 'SIMILAR_TO', model=SubsetRel)
    bert_is_next_to = RelationshipTo('RootWord', 'BERT_IS_NEXT_TO', model=SubsetRel)
    bert_is_on_top_of = RelationshipTo('RootWord', 'BERT_IS_ON_TOP_OF', model=SubsetRel)
    bert_is_underneath = RelationshipTo('RootWord', 'BERT_IS_UNDERNEATH', model=SubsetRel)
    bert_is_inside = RelationshipTo('RootWord', 'BERT_IS_INSIDE', model=SubsetRel)
    bert_is_bigger_than = RelationshipTo('RootWord', 'BERT_IS_BIGGER_THAN', model=SubsetRel)
    bert_is_smaller_than = RelationshipTo('RootWord', 'BERT_IS_SMALLER_THAN', model=SubsetRel)
    bert_they_verb = RelationshipTo('RootWord', 'BERT_THEY_VERB', model=SubsetRel)
    bert_they_verb_on = RelationshipTo('RootWord', 'BERT_THEY_VERB_ON', model=SubsetRel)
    bert_i_verb = RelationshipTo('RootWord', 'BERT_I_VERB', model=SubsetRel)
    bert_i_verb_on = RelationshipTo('RootWord', 'BERT_I_VERB_ON', model=SubsetRel)
    bert_is = RelationshipTo('RootWord', 'BERT_IS', model=SubsetRel)


class Object(Synset):
    def append_attribute(self, attr, value):
        self.__setattr__(attr, value)


class RootWordObject(RootWord):
    pass

class ModelHelper:

    @staticmethod
    def get_synset(synset):
        """
        Gets a synset from the db
        :param synset: A wordnet synset
        :return: The db representation of the synset
        """
        return Synset.nodes.get(name=synset.name())

    @staticmethod
    def add_or_get_synset(synset):
        """
        Adds or gets a synset from the db
        :param synset: A wordnet synset
        :return: The db representation of the synset
        """
        return Synset.get_or_create({'name': synset.name(), 'definition': synset.definition()})[0]

    @staticmethod
    def make_object(synset):
        synset.__class__ = Object
        synset.save()
        return synset

    @staticmethod
    def get_lemma(synset, lemma):
        """
        Gets a lemma from the db given a wordnet synset and one of it's lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        return Lemma.nodes.get(name=node_name)

    @staticmethod
    def add_or_get_lemma(synset, lemma):
        """
        Adds or gets a lemma from the database given a wordnet synset and it's lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        return Lemma.get_or_create(node_name)

    @staticmethod
    def get_object(synset):
        """
        Gets a synset:object from the db
        :param synset: A wordnet synset
        :return: The db representation of the synset:object
        """
        return Object.nodes.get(name=synset.name())

    @staticmethod
    def add_or_get_object(synset):
        """
        Adds or gets a synset:object from the db
        :param synset: A wordnet synset
        :return: The db representation of the synset:object
        """
        return Object.get_or_create(synset.name(), definition=synset.definition())

    @staticmethod
    def get_root_word(lemma):
        return RootWord.nodes.get(name=lemma.name())

    @staticmethod
    def newthing(orgfunction, addedstuff):
        props = orgfunction(aliases=False,properties=False)
        props.update(dict(
            (name, property) for name, property in addedstuff.items()
            if (False and isinstance(property, AliasProperty))
            or (False and isinstance(property, Property)
                and not isinstance(property, AliasProperty))
            or (True and isinstance(property, RelationshipDefinition))
        ))
        return props

    @staticmethod
    def add_dynamic_relationship(node: StructuredNode, attribute, object_name, relationship_name):
        value = RelationshipTo(object_name, relationship_name)
        node.__setattr__(attribute, value)
        #TODO: create lambda function and use kwargs properly
        props = ModelHelper.newthing(node.defined_properties,
                                     {attribute: value})
        node.defined_properties = lambda **kwargs: props
        node.__all_relationships__ = tuple(
            node.defined_properties(aliases=False, properties=False).items()
        )
        for key, val in node.__all_relationships__:
            node.__dict__[key] = val.build_manager(node, key)

    @staticmethod
    def add_dynamic_relationship_to_object(node, attribute, object_name, relationship_name):
        value = RelationshipTo(object_name, relationship_name)
        def __init__(self, *args, **kwargs):
            self.super.__init__(*args, **kwargs)
        news = type('Object1', (node,), {"__init__": __init__, attribute: value})
        news.__label__ = "Object"
        return news
