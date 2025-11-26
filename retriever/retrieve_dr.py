import sys
import os
import os.path as osp
import regex as re
import json
import asyncio
from typing import Set, Dict
import traceback
import collections as C

import aiofiles
import fire
from tqdm import tqdm
from loguru import logger
import networkx as nx
import numpy as np
import torch
from FlagEmbedding import BGEM3FlagModel
import matplotlib.pyplot as plt

from common.utils import format_doc_both, format_doc_only_if, format_doc_only_f


def main(
    model_path: str,                            # Path to the model
    save_path: str,                             # Path to the output
    data_root: str='./data/',                   # Path to the dataset root
    eval_set: str='proofnet',                   # The evaluation benchmark, should be either 'proofnet' or 'connf'
    query_instruction_for_retrieval: str='',    # Should be left blank (Unless otherwise embedder is SFTed w/ such instructions)
    k_max: int=100,                             # Max numbers of objects to retrieve
    batch_size: int=64,                         # Inference batch size
    verbose: bool=True                          # Whether to show verbose information
) -> None:
    os.makedirs(save_path, exist_ok=True)
    if (f'eval_result_{eval_set}.pt' in os.listdir(save_path) and f'retrieval_result_{eval_set}.pt' in os.listdir(save_path)):
        return

    logger.remove()
    logger.add(osp.join(save_path, 'eval.log'))
    logger.add(sys.stderr, level='DEBUG' if verbose else 'INFO')
    logger.info(f'Evaluating {model_path}')

    # Load premises
    with open(osp.join(data_root, eval_set, 'library.jsonl'), 'r') as f:
        premises = [json.loads(l) for l in f.readlines()]
    premises_ids = {v['full_name'] : i for i, v in enumerate(premises)}
    logger.debug(f'{len(premises)} Premises available')

    model_path = model_path.rstrip('/')
    if model_path.endswith('f+if'):
        format_doc = format_doc_both
        logger.warning('Using both formal and informal information to format document')
    elif model_path.endswith('f'):
        format_doc = format_doc_only_f
        logger.warning('Using only formal decls to format document')
    elif model_path.endswith('if'):
        format_doc = format_doc_only_if
        logger.warning('Using only informalizations to format document')
    else:
        raise RuntimeError(f'Invalid model name: {model_path}')

    premise_informalizations = [format_doc(p) for p in premises]   # No NOP token.

    # Load benchmark
    samples = []
    with open(osp.join(data_root, eval_set, 'benchmark.jsonl'), 'r') as f:
        for line in f.readlines():
            samples.append(json.loads(line))

    statement_informalizations = [query_instruction_for_retrieval + sample['informal_stmt'] for sample in samples]

    model = None
    # Embed premises
    try:
        premise_embeddings = torch.load(osp.join(save_path, 'premise_embeddings.pt'), weights_only=True)
        assert isinstance(premise_embeddings, np.ndarray)
        if premise_embeddings.shape[0] == len(premises) + 1:
            premise_embeddings = premise_embeddings[:-1]
        else:
            assert premise_embeddings.shape[0] == len(premises)
    except:
        model = BGEM3FlagModel(model_path, use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation
        
        premise_embeddings = model.encode(
            premise_informalizations,
            batch_size=batch_size,
            max_length=1024)['dense_vecs']
        torch.save(premise_embeddings, osp.join(save_path, 'premise_embeddings.pt'))

    # Embed statements
    try:
        statement_embeddings = torch.load(osp.join(save_path, f'{eval_set}_embeddings.pt'), weights_only=True)
        assert isinstance(statement_embeddings, np.ndarray) and statement_embeddings.shape[0] == len(statement_informalizations)
    except:
        if model is None:
            model = BGEM3FlagModel(model_path, use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation
        
        statement_embeddings = model.encode(
            statement_informalizations,
            batch_size=batch_size,
            max_length=1024)['dense_vecs']
        torch.save(statement_embeddings, osp.join(save_path, f'{eval_set}_embeddings.pt'))

    similarity = (torch.tensor(statement_embeddings).to(device=model.device, non_blocking=True).double() @ torch.tensor(premise_embeddings).to(device=model.device, non_blocking=True).double().T)
    top_kmax_similarities_all, top_kmax_indices_all = torch.topk(similarity, k_max)
    top_kmax_similarities_all = top_kmax_similarities_all.to(device='cpu', dtype=torch.float, non_blocking=True)
    top_kmax_indices_all = top_kmax_indices_all.to(device='cpu', non_blocking=True)
    top_kmax_similarities_dict = {
        v['full_name'] : top_kmax_similarities_all[i] for i, v in enumerate(samples)
    }
    top_kmax_indices_dict = {
        v['full_name'] : top_kmax_indices_all[i] for i, v in enumerate(samples)
    }
    torch.save((top_kmax_similarities_dict, top_kmax_indices_dict), osp.join(save_path, f'retrieval_result_{eval_set}.pt'))
    retrieval_gt = [sample['mathlib_dependencies'] for sample in samples]

    # Retrieval: Metric@k
    ks = torch.arange(1, k_max + 1)
    precision_k = torch.zeros(k_max, len(statement_informalizations))
    recall_k = torch.zeros(k_max, len(statement_informalizations))

    for i in tqdm(range(len(statement_informalizations)), desc='Computing k-metrics'):
        top_kmax_indices = top_kmax_indices_all[i].tolist()
        relevant_indices = set([premises_ids[x] for x in retrieval_gt[i]])
        
        if top_kmax_indices[0] == len(premises):
            # top_kmax_indices[0] == len(premises) denotes no premise should be retrieved
            precision_k[:, i] = int(len(relevant_indices) == 0)
            recall_k[:, i] = int(len(relevant_indices) == 0)
            continue

        for k in ks:
            retrieved_indices = top_kmax_indices[:k]
            relevant_count = len(relevant_indices.intersection(retrieved_indices))
            precision_k[k-1, i] = relevant_count / len(retrieved_indices)
            recall_k[k-1, i] = 0 if len(relevant_indices) == 0 else relevant_count / len(relevant_indices)
    
    torch.save((precision_k, recall_k), osp.join(save_path, f'eval_result_{eval_set}.pt'))

    if verbose:
        logger.debug(f'K\tPrecision\tRecall')
        for k in ks:
            logger.debug(f'{k}\t{precision_k[k-1].mean().item()}\t{recall_k[k-1].mean().item()}')
    if model is not None:
        del(model)    


if __name__ == '__main__':
    fire.Fire(main)
