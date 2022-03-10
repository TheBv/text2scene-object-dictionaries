from typing import Dict, List, Any

from fill_multiple_mask import FillMoreMaskPipeline
from transformers.pipelines.base import PipelineException
from transformers import AutoTokenizer, AutoModelForMaskedLM
from GraphModel import Object, Lemma, RootWord, RootWordObject
from neomodel import DoesNotExist
import torch
import argparse


tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
model = AutoModelForMaskedLM.from_pretrained("bert-base-cased", return_dict=True)
pipeline = None

# TODO: Rename self.sentences


"""
Class to manage the different bert target mask relationship types. Also fills sentences
"""


class RelationPrefab:
    def __init__(self, path):
        self.sentences = {}
        self.load_sentences(path)

    def load_sentences(self, path) -> None:
        """
        Loads all the predefined sentences from the specified file
        :param path: path to the relation file
        """
        sentence_list = []
        with open(path, 'r') as file:
            for line in file:
                if line.startswith("#"):
                    continue
                index = line.find(";")
                relation = {"sentence": line[0:index],
                            "relation_name": f"BERT_{line[index + 1:]}".rstrip()}
                sentence_list.append(relation)
        self.sentences = {"sentences": sentence_list}

    def get_filled_sentences(self, word: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Replaces the {target} with the specified word in every sentence
        :param word: The word that should be inserted
        :return: The sentences with the word in them
        """
        outsentences = []
        for item in self.sentences["sentences"]:
            sentence = {"sentence": item["sentence"].replace("{Target}", word), "relation_name":
                item["relation_name"]}
            outsentences.append(sentence)
        return {"sentences": outsentences}


def top_n_mask(json_data, args) -> dict:
    global tokenizer
    global model
    global pipeline
    top_k = 5
    targets = None
    masktoken = tokenizer.mask_token

    if 'sentences' in json_data:
        sentences = json_data['sentences']
    else:
        return {"error": "sentences are missing"}

    if "top_k" in json_data:
        top_k = int(json_data['top_k'])
    if "targets" in json_data:
        if len(json_data['targets']) > 0:
            targets = json_data['targets']

    # Platzhaltermaske durch Modellspezifische Maske austauschen
    model_inputs = [sent["sentence"].format(mask=masktoken) for sent in sentences]

    #  https://huggingface.co/transformers/_modules/transformers/pipelines/fill_mask.html
    if pipeline is None:
        if args.gpu_device != -1:
            pipeline = FillMoreMaskPipeline(model, tokenizer, device=0)
        else:
            pipeline = FillMoreMaskPipeline(model, tokenizer)
    try:
        results = pipeline(model_inputs, top_k=top_k, targets=targets)
    except PipelineException as e:
        return {"error": str(e)}

    for sent, result in zip(sentences, results):
        sent["results"] = result

    return {"sentences": sentences}


def main():
    """
    Iterates through all root object words and adds the bert relations
    """
    parser = argparse.ArgumentParser(description="Insert Bert relation data into the database")
    parser.add_argument('-gpu-device', help="Specify the gpu device to be used", default=-1,
                        dest="gpu_device", required=False, metavar="DEVICEID")
    parser.add_argument('-file', help="Specify the location of the relation file", required=True,
                        metavar="PATH")
    args = parser.parse_args()


    prefab = RelationPrefab(args.file)
    amount = len(list(RootWordObject.nodes))
    i = 0
    root_word: RootWordObject
    for root_word in RootWordObject.nodes:
        data = prefab.get_filled_sentences(root_word.name)
        if i % 200 == 0:
            print(f"Added Bert relations for {i}/{amount} items")
        i += 1
        if root_word.bert_is.single() is not None:
            continue
        results = top_n_mask(data, args)
        if "error" in results or "sentences" not in results:
            print(f"Couldn't process: {root_word.name}")
            continue
        for sentence in results["sentences"]:
            relation_name = sentence["relation_name"]
            for mask_result in sentence["results"]["mask_results"]:
                # TODO: Handle multiple masks
                for value in mask_result:
                    node_name = value["token_str"]
                    try:
                        nody = RootWord.nodes.get(name=node_name)
                        rel = root_word.__dict__[relation_name.lower()].connect(nody)
                        rel.weight = value["score"]
                        rel.save()
                    except DoesNotExist:
                        pass


if __name__ == "__main__":
    main()
