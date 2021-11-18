from neomodel import DoesNotExist
from nltk.corpus import wordnet as wn
import GraphModel
import nltk as nltk


class InsertHelper:

    def add_words_and_connect(self, graph_node_relation, additional_words):
        for additional_type in additional_words:
            node = self.add_word(additional_type)
            graph_node_relation.connect(node)

    def add_word(self, synset):
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
            lemma_node = self.add_lemma(synset, lemma)
            word.lemmas.connect(lemma_node)
        self.add_words_and_connect(word.hypernyms, synset.hypernyms())
        self.add_words_and_connect(word.hyponyms, synset.hyponyms())
        self.add_words_and_connect(word.member_holonyms, synset.member_holonyms())
        self.add_words_and_connect(word.root_hypernyms, synset.root_hypernyms())
        self.add_words_and_connect(word.member_holonyms, synset.member_holonyms())
        return word

    def add_lemma(self, synset, lemma):
        lemma_node = None
        node_name = """{}.{}""".format(synset.name(), lemma.name())
        try:
            lemma_node = GraphModel.Lemma.nodes.get(name=node_name)
            return lemma_node
        except DoesNotExist:
            lemma_node = GraphModel.Lemma(name=node_name)
            lemma_node.save()
        for antonym in lemma.antonyms():
            antonym = self.add_lemma(antonym.synset(), antonym)
            lemma_node.antonyms.connect(antonym)
        for pertainym in lemma.pertainyms():
            pertainym = self.add_lemma(pertainym.synset(), pertainym)
            lemma_node.pertainyms.connect(pertainym)
        return lemma_node


insert_helper = InsertHelper()
i = 0
for synset in wn.all_synsets():
    insert_helper.add_word(synset)
    i += 1
    if i % 100 == 0:
        print(i)

