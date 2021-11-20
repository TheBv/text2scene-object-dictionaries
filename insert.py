from neomodel import DoesNotExist
from nltk.corpus import wordnet as wn
import GraphModel
import argparse

parser = argparse.ArgumentParser(description="Insert Wordnet data into neo4j")
parser.add_argument('--a', help="Parser everything into the database", const=True, nargs='?')
parser.add_argument('--r', help="Update/Insert the relations", const=True, nargs='?')
parser.add_argument('--n', help="Parse only the nodes into the database", const=True, nargs='?')


class InsertHelper:

    def add_synsets_and_connect_relationships(self, graph_node_relation, additional_words: list):
        """
        Takes an existing nodes connection attribute and adds all the words in the
        additional_words list recursively to the db if they don't exist yet. Then connect them to
        the given relation
        :param graph_node_relation: A nodes connection attribute
        :param additional_words: A list of synsets
        """
        for additional_type in additional_words:
            node = self.add_synset_and_relationships(additional_type)
            graph_node_relation.connect(node)

    def add_synset_and_connect(self, graph_node_relation, additional_synsets: list):
        """
        Adds all synsets in the additional_synsets list to the db then connect them to the relation
        that's being provided
        :param graph_node_relation: A nodes connection attribute
        :param additional_synsets: A list of synsets
        """
        for additional_type in additional_synsets:
            node = self.get_or_create_synset(additional_type)
            graph_node_relation.connect(node)

    @staticmethod
    def batch_create_synset(synsets: list):
        """
        Adds all synsets in the list and their lemmas to the database
        :param synsets: A list of synsets to be added
        """
        words = []
        lemmas = []
        for synset in synsets:
            words.append({"name": synset.name(), "definition": synset.definition()})
            for lemma in synset.lemmas():
                node_name = """{}.{}""".format(synset.name(), lemma.name())
                lemmas.append({"name": node_name})
        GraphModel.Synset.create_or_update(*words)
        GraphModel.Lemma.create_or_update(*lemmas)

    def get_or_create_synset(self, synset):
        """
        Either gets the synset from the db or adds it and the lemma to it
        :param synset: A synset
        :return:
        """
        word = None
        try:
            word = self.get_synset(synset)
            return word
        except DoesNotExist:
            word = GraphModel.Synset(name=synset.name(), definition=synset.definition())
            # Make sure we save the word to discourage infinite recursion
            word.save()
        # Add all the lemmas
        for lemma in synset.lemmas():
            self.add_or_get_lemma(synset, lemma)
        return word

    @staticmethod
    def get_synset(synset):
        """
        Gets a synset from the db
        :param synset: A wordnet synset
        :return: A db synset
        """
        return GraphModel.Synset.nodes.get(name=synset.name())

    @staticmethod
    def add_or_get_lemma(synset, lemma):
        """
        Adds or gets a lemma from the database given a wordnet synset and it's lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        try:
            lemma_node = GraphModel.Lemma.nodes.get(name=node_name)
            return lemma_node
        except DoesNotExist:
            lemma_node = GraphModel.Lemma(name=node_name)
            lemma_node.save()
            return lemma_node

    @staticmethod
    def get_lemma(synset, lemma):
        """
        Gets a lemma from the db given a wordnet synset and one of it's lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        return GraphModel.Lemma.nodes.get(name=node_name)

    def add_synset_and_relationships(self, synset):
        """
        Adds a wordnet synset as well as all of it's relationships, recursively into the db
        :param synset: A wordnet synset
        :return: The db representation of that synset
        """
        try:
            word = GraphModel.Synset.nodes.get(name=synset.name())
            return word
        except DoesNotExist:
            word = GraphModel.Synset(name=synset.name(), definition=synset.definition())
            # Make sure we save the word to discourage infinite recursion
            word.save()
        lemmas = synset.lemmas()
        # Add all the lemmas
        for lemma in lemmas:
            lemma_node = self.add_or_get_lemma(synset, lemma)
            word.lemmas.connect(lemma_node)
        self.add_synsets_and_connect_relationships(word.hypernyms, synset.hypernyms())
        self.add_synsets_and_connect_relationships(word.hyponyms, synset.hyponyms())
        self.add_synsets_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        self.add_synsets_and_connect_relationships(word.root_hypernyms, synset.root_hypernyms())
        self.add_synsets_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        return word

    def add_lemma_and_relationships(self, synset, lemma):
        """
        Adds a wordnet lemma as well as all of it's relationships, recursively into the db
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        try:
            lemma_node = GraphModel.Lemma.nodes.get(name=node_name)
            return lemma_node
        except DoesNotExist:
            lemma_node = GraphModel.Lemma(name=node_name)
            lemma_node.save()
        for antonym in lemma.antonyms():
            antonym = self.add_or_get_lemma(antonym.synset(), antonym)
            lemma_node.antonyms.connect(antonym)
        for pertainym in lemma.pertainyms():
            pertainym = self.add_or_get_lemma(pertainym.synset(), pertainym)
            lemma_node.pertainyms.connect(pertainym)
        return lemma_node

    def set_synset_relationships(self, synset):
        """
        Sets the relationships of the corresponding db synset given a wordnet synset
        :param synset: A wordnet synset
        :return: None
        """
        try:
            word = self.get_synset(synset)
            lemmas = synset.lemmas()
            # Add all the lemmas
            for lemma in lemmas:
                lemma_node = self.get_lemma(synset, lemma)
                word.lemmas.connect(lemma_node)
            self.add_synset_and_connect(word.hypernyms, synset.hypernyms())
            self.add_synset_and_connect(word.hyponyms, synset.hyponyms())
            self.add_synset_and_connect(word.member_holonyms, synset.member_holonyms())
            self.add_synset_and_connect(word.root_hypernyms, synset.root_hypernyms())
            self.add_synset_and_connect(word.member_holonyms, synset.member_holonyms())
        except DoesNotExist:
            return

    def set_lemma_relationships(self, synset, lemma):
        """
        Sets the relationships of the corresponding db lemma given a wordnet lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: None
        """
        try:
            lemma_node = self.get_lemma(synset, lemma)
            for antonym in lemma.antonyms():
                antonym = self.get_lemma(antonym.synset(), antonym)
                lemma_node.antonyms.connect(antonym)
            for pertainym in lemma.pertainyms():
                pertainym = self.get_lemma(pertainym.synset(), pertainym)
                lemma_node.pertainyms.connect(pertainym)
        except DoesNotExist:
            return


def parse_nodes(wordlist: list):
    insert_helper = InsertHelper()
    i = 0
    n = 400
    print("PARSING NODES")
    for i in range(0, len(wordlist), n):
        insert_helper.batch_create_synset(wordlist[i:i + n])
        i += n
        if i % n == 0:
            print(i)


def parse_relationships(wordlist: list):
    insert_helper = InsertHelper()
    i = 0
    print("ADDING RELATIONSHIPS")
    for synset in wordlist:
        insert_helper.set_synset_relationships(synset)
        i += 1
        if i % 100 == 0:
            print(i)


args = parser.parse_args()

if args.a is not None:
    synset = wn.all_synsets()
    parse_nodes(list(synset))
    parse_relationships(synset)
elif args.n is not None:
    synset = wn.all_synsets()
    parse_nodes(list(synset))
elif args.r is not None:
    synset = wn.all_synsets()
    parse_relationships(synset)