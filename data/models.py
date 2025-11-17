import torch
from transformers import BertForSequenceClassification, BertTokenizer


class SentimentModel:

    def __init__(self):
        model_path = "ProsusAI/finbert"
        self._model = BertForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = BertTokenizer.from_pretrained(model_path)


if __name__ == '__main__':
    model = SentimentModel()