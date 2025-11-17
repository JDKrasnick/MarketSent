import torch
from transformers import BertForSequenceClassification, BertTokenizer


class SentimentPipeline:

    @staticmethod
    def analyze(self, text):
        input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        outputs = self._model(**input)
        scores = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().numpy()

        return scores



if __name__ == '__main__':
    pass