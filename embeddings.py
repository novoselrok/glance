from typing import List

import numpy as np
import torch
import torch.nn.functional as F
from transformers import BertModel, BertTokenizer


def mean_pool(
    last_hidden_states: torch.Tensor, attention_mask: torch.Tensor
) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def embed(encoder_model, inputs):
    model_output = encoder_model(**inputs)
    embeddings = mean_pool(model_output.last_hidden_state, inputs["attention_mask"])
    return F.normalize(embeddings, p=2, dim=1)


def e5_model_embeddings(
    model: BertModel,
    tokenizer: BertTokenizer,
    samples: List[str],
    max_seq_length=512,
    batch_size=32,
    device="cpu",
) -> np.ndarray:
    passage_prefix = "passage: "
    augmented_samples = [f"{passage_prefix}{sample}" for sample in samples]

    embeddings = []
    for start in range(0, len(augmented_samples), batch_size):
        batch = augmented_samples[start : start + batch_size]

        encoded_samples = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_seq_length,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            batch_embeddings = embed(model, encoded_samples)
            embeddings.append(batch_embeddings.cpu().numpy())

    return np.vstack(embeddings)
