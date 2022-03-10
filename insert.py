from gensim.models.fasttext import FastTextKeyedVectors
from neomodel import DoesNotExist, db
from nltk.corpus import wordnet as wn
from GraphModel import ModelHelper, Lemma, Synset, RootWord, Object
from gensim.models import FastText
from gensim.test.utils import datapath
import argparse


class InsertHelper:

    def __init__(self):
        self.wv: FastTextKeyedVectors = None

    def setup_wordvectors(self):
        corpus_file = datapath('lee_background.cor')
        model = FastText(vector_size=100)
        model.build_vocab(corpus_file=corpus_file)
        model.train(
            corpus_file=corpus_file, epochs=model.epochs,
            total_examples=model.corpus_count, total_words=model.corpus_total_words,
        )
        self.wv = model.wv

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

    @staticmethod
    def add_synset_and_connect(graph_node_relation, additional_synsets: list):
        """
        Adds all synsets in the additional_synsets list to the db then connect them to the relation
        that's being provided
        :param graph_node_relation: A nodes connection attribute
        :param additional_synsets: A list of synsets
        """
        for additional_type in additional_synsets:
            node = ModelHelper.add_or_get_synset(additional_type)
            graph_node_relation.connect(node)

    @staticmethod
    def get_synsets_and_connect(graph_node_relation, additional_synsets: list):
        """
        Adds all synsets in the additional_synsets list to the db then connect them to the relation
        that's being provided
        :param graph_node_relation: A nodes connection attribute
        :param additional_synsets: A list of synsets
        """
        for additional_type in additional_synsets:
            try:
                node = ModelHelper.get_synset(additional_type)
                graph_node_relation.connect(node)
            except DoesNotExist:
                print("Couldn't find node", additional_type)

    @staticmethod
    def batch_create_synset(synsets: list):
        """
        Adds all synsets in the list and their lemmas to the database
        :param synsets: A list of synsets to be added
        """
        words = []
        lemmas = []
        root_words = []
        for synset in synsets:
            words.append({"name": synset.name(), "definition": synset.definition()})
            for lemma in synset.lemmas():
                node_name = """{}.{}""".format(synset.name(), lemma.name())
                lemmas.append({"name": node_name})
                root_words.append({"name": lemma.name()})
        Synset.create_or_update(*words)
        Lemma.create_or_update(*lemmas)
        RootWord.create_or_update(*root_words)

    def add_synset_and_relationships(self, synset):
        """
        Adds a wordnet synset as well as all of it's relationships, recursively into the db
        :param synset: A wordnet synset
        :return: The db representation of that synset
        """
        try:
            word = Synset.nodes.get(name=synset.name())
            return word
        except DoesNotExist:
            word = Synset(name=synset.name(), definition=synset.definition())
            # Make sure we save the word to discourage infinite recursion
            word.save()
        lemmas = synset.lemmas()
        # Add all the lemmas
        for lemma in lemmas:
            lemma_node = ModelHelper.add_or_get_lemma(synset, lemma)
            word.lemmas.connect(lemma_node)
        self.add_synsets_and_connect_relationships(word.hypernyms, synset.hypernyms())
        self.add_synsets_and_connect_relationships(word.hyponyms, synset.hyponyms())
        self.add_synsets_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        self.add_synsets_and_connect_relationships(word.root_hypernyms, synset.root_hypernyms())
        self.add_synsets_and_connect_relationships(word.member_holonyms, synset.member_holonyms())
        return word

    @staticmethod
    def add_lemma_and_relationships(synset, lemma):
        """
        Adds a wordnet lemma as well as all of it's relationships, recursively into the db
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: The db representation of the lemma
        """
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        try:
            lemma_node = Lemma.nodes.get(name=node_name)
            return lemma_node
        except DoesNotExist:
            lemma_node = Lemma(name=node_name)
            lemma_node.save()
        for antonym in lemma.antonyms():
            antonym = ModelHelper.add_or_get_lemma(antonym.synset(), antonym)
            lemma_node.antonyms.connect(antonym)
        for pertainym in lemma.pertainyms():
            pertainym = ModelHelper.add_or_get_lemma(pertainym.synset(), pertainym)
            lemma_node.pertainyms.connect(pertainym)
        return lemma_node

    def set_synset_relationships(self, synset):
        """
        Sets the relationships of the corresponding db synset given a wordnet synset
        :param synset: A wordnet synset
        :return: None
        """
        try:
            word = ModelHelper.get_synset(synset)
            lemmas = synset.lemmas()
            # Add all the lemmas
            for lemma in lemmas:
                lemma_node = ModelHelper.get_lemma(synset, lemma)
                root_word_node = ModelHelper.get_root_word(lemma)
                # Connect root word and lemma
                lemma_node.root_word.connect(root_word_node)
                root_word_node.contains.connect(lemma_node)
                # Connect word with lemma
                word.lemmas.connect(lemma_node)
            self.get_synsets_and_connect(word.hypernyms, synset.hypernyms())
            self.get_synsets_and_connect(word.hyponyms, synset.hyponyms())
            self.get_synsets_and_connect(word.member_holonyms, synset.member_holonyms())
            self.get_synsets_and_connect(word.root_hypernyms, synset.root_hypernyms())
            self.get_synsets_and_connect(word.member_holonyms, synset.member_holonyms())
        except DoesNotExist:
            return

    @staticmethod
    def set_lemma_relationships(synset, lemma):
        """
        Sets the relationships of the corresponding db lemma given a wordnet lemma
        :param synset: A wordnet synset
        :param lemma: A wordnet lemma that's part of the provided synset
        :return: None
        """
        try:
            lemma_node = ModelHelper.get_lemma(synset, lemma)
            for antonym in lemma.antonyms():
                antonym = ModelHelper.get_lemma(antonym.synset(), antonym)
                lemma_node.antonyms.connect(antonym)
            for pertainym in lemma.pertainyms():
                pertainym = ModelHelper.get_lemma(pertainym.synset(), pertainym)
                lemma_node.pertainyms.connect(pertainym)
        except DoesNotExist:
            return

    @staticmethod
    def classify_objects():
        db.cypher_query("""match p = (n)-[r:HAS_HYPERNYM*1..]->(child) where child.name = 
        "artifact.n.01" SET n:Object""")

    # @staticmethod
    # def classify_root_words():
    #     db.cypher_query("""Match (m:Synset)-[r]->(n:Lemma) With
    #         right(n.name, apoc.text.indexOf(reverse(n.name),'.')) as newName,
    #         n as oldNode
    #         MERGE (k:RootWord{name:newName})
    #         CREATE (oldNode)-[r:SUBSET_OF]->(k)""")

    @staticmethod
    def classify_root_word_objects():
        db.cypher_query("""Match (:Object)-[k:HAS_LEMMA]-(l:Lemma)-[r:SUBSET_OF]->(o:RootWord)
         set o:RootWordObject""")

    def add_wv_relations(self):
        if self.wv is None:
            self.setup_wordvectors()
        count = 0
        object_word: Object
        for object_word in Object.nodes:
            lemma_word: Lemma
            for lemma_word in object_word.lemmas:
                for root_word in lemma_word.root_word:
                    for (word, score) in self.wv.most_similar(root_word.name):
                        try:
                            model_word = RootWord.nodes.get(name=word)
                            rel = root_word.similar.connect(model_word)
                            rel.weight = score
                            rel.save()
                        except DoesNotExist:
                            pass
            count += 1
            if count % 100 == 0:
                print(count)


def parse_nodes(wordlist: list):
    insert_helper = InsertHelper()
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
        for lemma in synset.lemmas():
            insert_helper.set_lemma_relationships(synset, lemma)
        i += 1
        if i % 100 == 0:
            print(i)


def main():
    parser = argparse.ArgumentParser(description="Insert Wordnet data into neo4j")
    parser.add_argument('--a', help="Parser everything into the database", const=True, nargs='?')
    parser.add_argument('--wr', help="Add all wordvector relations", const=True, nargs='?')
    args = parser.parse_args()

    if args.a is not None:
        synset = wn.all_synsets()
        print("Inserting wordnet data")
        parse_nodes(list(synset))
        print("Inserting relationships")
        parse_relationships(synset)
        print("Classifying objects")
        insert_helper = InsertHelper()
        insert_helper.classify_objects()
        print("Classifying RootWord objects")
        insert_helper.classify_root_word_objects()
    if args.wr is not None:
        print("Adding wordvector relations")
        insert_helper = InsertHelper()
        insert_helper.add_wv_relations()


if __name__ == "__main__":
    main()
