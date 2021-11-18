from neomodel import DoesNotExist
from nltk.corpus import wordnet as wn
import GraphModel
import argparse

parser = argparse.ArgumentParser(description="Insert Wordnet data into neo4j")
parser.add_argument('--a', help="Parser everything into the database", const=True, nargs='?')
parser.add_argument('--r', help="Update/Insert the relations", const=True, nargs='?')
parser.add_argument('--n', help="Parse only the nodes into the database", const=True, nargs='?')


class InsertHelper:

    def add_words_and_connect_relationships(self, graph_node_relation, additional_words):
        for additional_type in additional_words:
            node = self.add_word_and_relationships(additional_type)
            graph_node_relation.connect(node)

    def add_word_and_connect(self, graph_node_relation, additional_words):
        for additional_type in additional_words:
            node = self.get_or_create_word(additional_type)
            graph_node_relation.connect(node)

    @staticmethod
    def batch_get_or_create_word(synsets: list):
        words = []
        lemmas = []
        for synset in synsets:
            words.append({"name": synset.name(), "definition": synset.definition()})
            for lemma in synset.lemmas():
                node_name = """{}.{}""".format(synset.name(), lemma.name())
                lemmas.append({"name": node_name})
        GraphModel.Word.create_or_update(*words)
        GraphModel.Lemma.create_or_update(*lemmas)

    def get_or_create_word(self, synset):
        word = None
        try:
            word = self.get_word(synset)
            return word
        except DoesNotExist:
            word = GraphModel.Word(name=synset.name(), definition=synset.definition())
            # Make sure we save the word to discourage infinite recursion
            word.save()
        # Add all the lemmas
        for lemma in synset.lemmas():
            self.add_or_get_lemma(synset, lemma)
        return word

    @staticmethod
    def get_word(synset):
        return GraphModel.Word.nodes.get(name=synset.name())

    @staticmethod
    def add_or_get_lemma(synset, lemma):
        lemma_node = None
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
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        return GraphModel.Lemma.nodes.get(name=node_name)

    def add_word_and_relationships(self, synset):
        word = None
        try:
            word = GraphModel.Word.nodes.get(name=synset.name())
            return word
        except DoesNotExist:
            word = GraphModel.Word(name=synset.name(), definition=synset.definition())
            # Make sure we save the word to discourage infinite recursion
            word.save()
        lemmas = synset.lemmas()
        # Add all the lemmas
        for lemma in lemmas:
            lemma_node = self.add_or_get_lemma(synset, lemma)
            word.lemmas.connect(lemma_node)
        self.add_words_and_connect_relationships(word.hypernyms, synset.hypernyms())
        self.add_words_and_connect_relationships(word.hyponyms, synset.hyponyms())
        self.add_words_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        self.add_words_and_connect_relationships(word.root_hypernyms, synset.root_hypernyms())
        self.add_words_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        return word

    def add_lemma_and_relationships(self, synset, lemma):
        lemma_node = None
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

    def set_word_relationships(self, synset):
        try:
            word = self.get_word(synset)
            lemmas = synset.lemmas()
            # Add all the lemmas
            for lemma in lemmas:
                lemma_node = self.get_lemma(synset, lemma)
                word.lemmas.connect(lemma_node)
            self.add_word_and_connect(word.hypernyms, synset.hypernyms())
            self.add_word_and_connect(word.hyponyms, synset.hyponyms())
            self.add_word_and_connect(word.member_holonyms, synset.member_holonyms())
            self.add_word_and_connect(word.root_hypernyms, synset.root_hypernyms())
            self.add_word_and_connect(word.member_holonyms, synset.member_holonyms())
        except DoesNotExist:
            return

    def set_lemma_relationships(self, synset, lemma):
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
        insert_helper.batch_get_or_create_word(wordlist[i:i+n])
        i += n
        if i % n == 0:
            print(i)


def parse_relationships(wordlist: list):
    insert_helper = InsertHelper()
    i = 0
    print("ADDING RELATIONSHIPS")
    for synset in wordlist:
        insert_helper.set_word_relationships(synset)
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