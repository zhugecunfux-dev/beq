import os
import sys
import os.path as osp
import re
import json
import asyncio
import aiohttp
from typing import Set, Dict, List, Optional
import traceback
from copy import deepcopy
import requests
import psutil
import multiprocessing as mp
import regex as re
import collections as C

import pprint
import aiofiles
import argparse
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
import vllm
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine, AsyncEngineDeadError
from vllm.sampling_params import SamplingParams
from vllm.usage.usage_lib import UsageContext
from vllm.utils import random_uuid, iterate_with_cancellation
import torch
from transformers import AutoTokenizer
import fire
from easydict import EasyDict
from openai import OpenAI, AsyncOpenAI
from tqdm import tqdm
from loguru import logger

from common.constants import INIT_WAIT_TIME
from common.dataclasses import Environment
from common.repl import REPL


TIMEOUT_KEEP_ALIVE = 5  # seconds.
app = FastAPI()
engine = None

THM_CODE_PATTERN = re.compile(r'theorem (.*?)sorry', flags=re.DOTALL)
CODEBLOCK_PATTERN = re.compile(r'```(?:.*?)\n(.*?)```', flags=re.DOTALL)

BACKTRANSLATION_PROMPT_TEMPLATE = """Given a Lean 4 theorem, please **briefly** and **consisely** explain it in natural language in one line.
Here are some examples:

Code:
```
theorem putnam_1964_b3
(f : ℝ → ℝ)
(hf : Continuous f ∧ ∀ α > 0, Tendsto (fun n : ℕ ↦ f (n * α)) atTop (𝓝 0))
: (Tendsto f atTop (𝓝 0)) := sorry
```
Summarization: Suppose $f : \\mathbb{R} \\to \\mathbb{R}$ is continuous and for every $\\alpha > 0$, $\\lim_{n \\to \\infty} f(n\\alpha) = 0$. Prove that $\\lim_{x \\to \\infty} f(x) = 0$.

---

Code:
```
theorem putnam_1968_b2
[Group G]
(hG : Finite G)
(A : Set G)
(hA : A.ncard > (Nat.card G : ℚ)/2)
: ∀ g : G, ∃ x ∈ A, ∃ y ∈ A, g = x * y := by sorry
```
Summarization: Let $G$ be a finite group (with a multiplicative operation), and $A$ be a subset of $G$ that contains more than half of $G$'s elements. Prove that every element of $G$ can be expressed as the product of two elements of $A$.

---

Code:
```
theorem putnam_2022_a3
(p : ℕ)
(hp : Nat.Prime p ∧ p > 5)
(f : ℕ := {a : ℕ → (ZMod p) | ∀ n : ℕ, a n ≠ 0 ∧ a n * a (n + 2) = 1 + a (n + 1)}.ncard)
: f ≡ 0 [MOD 5] ∨ f ≡ 2 [MOD 5] := sorry
```
Summarization: Let $p$ be a prime number greater than 5. Let $f(p)$ denote the number of infinite sequences $a_1, a_2, a_3, \\dots$ such that $a_n \\in \\{1, 2, \\dots, p-1\\}$ and $a_n a_{n+2} \\equiv 1 + a_{n+1} \\pmod{p}$ for all $n \\geq 1$. Prove that $f(p)$ is congruent to 0 or 2 $\\pmod{5}$.

Please **briefly** and **consisely** explain the following theorem in one line:
Code:
```
{THM_CODE}
```
Summarization: 
"""

EQUIV_DETERMINATION_PROMPT_TEMPLATE = """Please check following two math problems is same or different? Please consider each statement in two problems, they are different if any statement is different. Please point out any differences you found. Please reply **same** or **different** in the final sentence with bold format.

Problem 1: {THM_1}

Problem 2: {THM_2}
"""

def extract_first_code_block(text):
    matches = re.findall(CODEBLOCK_PATTERN, text)
    return matches[0]

def unique(r : list) -> list:
    s = []
    for i in r:
        if i not in s:
            s.append(i)
    return s

async def async_generate_vllm(tokenizer, input_prompt, url, sampling_params: Dict):
    final_output = None
    prompt = tokenizer.apply_chat_template([
        {
            "role": "system",
            "content": "You are an expert on Lean 4 and Isabelle."
        },
        {
            "role": "user",
            "content": input_prompt
        },
    ], tokenize=False)
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(60 * 60)) as session:
        async with session.post(
            url,
            json=dict(
                prompt=prompt,
                **sampling_params
            )
        ) as response:
            try:
                final_output = EasyDict(
                    await response.json()
                )
            except Exception as e:
                logger.error(f'Error {[traceback.format_exc()]} when parsing {[response.content]}.')
            assert final_output is not None
    
    return final_output


def main(
        async_generate,
        model_path: str,
        eval_set: str,
        working_root: str,
        dataset_root: str,
        url: str,
        try_num: int=8,
        num_concurrency: int=16,
        max_tokens: int=512,
        temperature: Optional[float]=None
        ):
    if temperature is None:
        temperature = 0.0 if try_num == 1 else 0.7
    
    saved_args = {**locals()}
    os.makedirs(working_root, exist_ok=True)
    logger.add(osp.join(working_root, 'autoformalization_equiv_checked_llm_qwen.log'))
    logger.info(f'hyperparameters: {saved_args}')
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    with open(osp.join(dataset_root, eval_set, 'library.jsonl'), 'r') as f:
        premises_with_informalization = [json.loads(l) for l in f.readlines()]
    premises_dict = {p['full_name'] : p for p in premises_with_informalization}

    samples = []
    with open(osp.join(dataset_root, eval_set, 'benchmark.jsonl'), 'r') as f:
        for line in f.readlines():
            samples.append(json.loads(line))
    # ['informal_stmt', 'formal_stmt', 'header', 'proof_state', 'mathlib_dependencies', 'hard_dependencies', 'source', 'problem_name']

    loop = asyncio.get_event_loop()
    autoformalization_result = dict()

    try:
        # Load result recording
        assert osp.exists(osp.join(working_root, f'autoformalization.json')) and osp.isfile(osp.join(working_root, f'autoformalization.json'))
        logger.info(f'Loading autoformalization result from {osp.join(working_root, "autoformalization.json")}...')
        with open(osp.join(working_root, f'autoformalization.json'), 'r') as f:
            autoformalization_result = json.load(f)
        
        async def check_equivalence(problem_name: str, code_P: str, code_Q: str):
            # P-Q equivalence
            assert ('theorem thm_P' in code_P) and ('theorem thm_Q' in code_Q)
            code_P = code_P.replace('theorem thm_P', 'theorem example').strip()
            code_Q = code_Q.replace('theorem thm_Q', 'theorem example').strip()
            assert code_Q.endswith('sorry')

            # LLM exact
            for i in range(try_num):
                informalization_P, informalization_Q = await asyncio.gather(*[
                    async_generate(
                        tokenizer,
                        input_prompt=BACKTRANSLATION_PROMPT_TEMPLATE.replace('{THM_CODE}', code_P),
                        url=url+'/generate',
                        sampling_params=dict(
                            n=1,
                            max_tokens=max_tokens,
                            temperature=temperature,
                        )
                    ),
                    async_generate(
                        tokenizer,
                        input_prompt=BACKTRANSLATION_PROMPT_TEMPLATE.replace('{THM_CODE}', code_Q),
                        url=url+'/generate',
                        sampling_params=dict(
                            n=1,
                            max_tokens=max_tokens,
                            temperature=temperature,
                        )
                    ),
                ])
                if len(informalization_P.outputs[0].text) < 10 or len(informalization_Q.outputs[0].text) < 10:
                    logger.info('Informalization too short, retry.')
                    continue
                input_prompt = EQUIV_DETERMINATION_PROMPT_TEMPLATE.replace('{THM_1}', informalization_P.outputs[0].text).replace('{THM_2}', informalization_Q.outputs[0].text)
                final_output = await async_generate(
                    tokenizer,
                    input_prompt=input_prompt,
                    url=url+'/generate',
                    sampling_params=dict(
                        n=1,
                        max_tokens=max_tokens,
                        temperature=temperature,

                    ) | (
                        dict() if url.endswith('/stop') else dict(
                            # use_beam_search=(temperature == 0.0 and try_num > 1),
                            stop='<|im_end|>'
                        )
                    )
                )
                assert len(final_output.outputs) == 1
                output = final_output.outputs[0]

                if len(final_output.outputs) != 1:
                    logger.warning(f'check_equivalence({problem_name}): len(final_output.outputs) != 1, retrying.')
                    continue

                final_sentence = output.text.strip().split('\n')[-1]
                same_cnt = len(re.findall(r'\*\*same\*\*', final_sentence))
                different_cnt = len(re.findall(r'\*\*different\*\*', final_sentence))
                if same_cnt + different_cnt != 1:
                    logger.warning(f'check_equivalence({problem_name}): result parsing failed with "{input_prompt}\n\n{final_sentence}", retrying.')
                    continue    # Wrong format, neglect
                
                return (same_cnt > different_cnt), [o.text for o in final_output.outputs]
            logger.error('Retry number limit exceeded.')
            return True, ['']

        async def check(sample: Dict):
            # sample: ['informal_stmt', 'formal_stmt', 'header', 'proof_state', 'mathlib_dependencies', 'hard_dependencies', 'source', 'problem_name']
            class_name, problem_name = sample['source'], sample['problem_name']
            formal_stmt_gt = sample['formal_stmt']
            formal_stmt_gt = formal_stmt_gt.replace(f'theorem {problem_name}', 'theorem thm_P') # Assuming thm_P

            for try_i, cur_result in enumerate(autoformalization_result[sample['full_name']]):
                try:
                    if 'typecheck_result' not in cur_result.keys():
                        logger.warning(f'Check({class_name}.{problem_name}, {try_i}/{len(autoformalization_result[sample["full_name"]])}): Missing typecheck result')
                        continue
                    elif not cur_result['typecheck_result']['is_success']:
                        continue

                    # EquivCheck
                    formal_stmt_pred = cur_result['formal_stmt_pred']   # Assuming thm_Q
                    # P-Q equivalence
                    try:
                        is_equivalent, result = await check_equivalence(
                            f'{class_name}.{problem_name}_equiv_PQ',
                            formal_stmt_gt,
                            formal_stmt_pred
                            )
                    except:
                        is_equivalent, result = False, None
                        logger.error(f'Check({class_name}.{problem_name}, {try_i}/{len(autoformalization_result[sample["full_name"]])}): Equivalence checking error with {traceback.format_exc()}')
                    
                    cur_result['equivcheck_results'] = {
                        'is_success': is_equivalent,
                        'result': result
                    }
                    if is_equivalent:
                        logger.info(f'Check({class_name}.{problem_name}, {try_i}/{len(autoformalization_result[sample["full_name"]])}): Equivalence check succeeded')
                    else:
                        logger.info(f'Check({class_name}.{problem_name}, {try_i}/{len(autoformalization_result[sample["full_name"]])}): Equivalence check failed.')
                
                except Exception as e:
                    logger.debug(f'Check({class_name}.{problem_name}, {try_i}/{len(autoformalization_result[sample["full_name"]])}): Failed with {e}')
                    pass

            typecheck_successes = [r for r in autoformalization_result[sample['full_name']] if 'typecheck_result' in r.keys() and r['typecheck_result']['is_success']]
            equiv_successes = [i for i, r in enumerate(typecheck_successes) if 'equivcheck_results' in r.keys() and r['equivcheck_results']['is_success']]
            logger.info(f'Check({class_name}.{problem_name}): Success Count of (T, Equiv): {len(typecheck_successes)} {len(equiv_successes)}')

        async def _async_main():
            pending_tasks: Set[asyncio.Task] = set()
            for i, v in tqdm(enumerate(samples)):
                if v['full_name'] not in autoformalization_result.keys():
                    logger.warning(f'Main(): Missing autoformalization result for {v["full_name"]}')
                    continue
                if len(pending_tasks) >= num_concurrency:
                    done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                pending_tasks.add(
                    asyncio.create_task(
                        check(v)
                    )
                )
            if len(pending_tasks) > 0:
                await asyncio.wait(pending_tasks)
            await logger.complete()

        # asyncio.run(_async_main())
        loop.run_until_complete(_async_main())

    finally:
        try:
            with open(osp.join(working_root, f'autoformalization_equiv_checked_llm_qwen.json'), 'w') as f:
                json.dump(autoformalization_result, f)
            response = requests.post(
                url=url+ ('/stop' if not url.endswith('/stop') else ''), json=''
            )
        except Exception as e:
            logger.warning(f'Server ended with {e}')


@app.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@app.post("/generate")
async def generate(request: Request) -> Response:
    """Generate completion for the request.

    The request should be a JSON object with the following fields:
    - prompt: the prompt to use for the generation.
    - stream: whether to stream the results or not.
    - other fields: the sampling parameters (See `SamplingParams` for details).
    """
    request_dict = await request.json()
    prompt = request_dict.pop("prompt")
    sampling_params = SamplingParams(**request_dict)
    sampling_params.logprobs = True
    request_id = random_uuid()

    assert engine is not None
    results_generator = engine.generate(prompt, sampling_params, request_id)
    results_generator = iterate_with_cancellation(
        results_generator, is_cancelled=request.is_disconnected)

    # Non-streaming case
    final_output = None
    try:
        async for request_output in results_generator:
            final_output = request_output
    except asyncio.CancelledError:
        return Response(status_code=499)

    assert final_output is not None
    prompt = final_output.prompt
    assert prompt is not None
    return JSONResponse(dict(
        outputs=[dict(
            text=o.text,
            cumulative_logprob=o.cumulative_logprob,
            token_ids=list(o.token_ids),
            finish_reason=o.finish_reason
        ) for o in final_output.outputs]
    ))

@app.post("/stop")
async def stop(request: Request) -> Response:
    """Generate completion for the request.

    The request should be a JSON object with the following fields:
    - prompt: the prompt to use for the generation.
    - stream: whether to stream the results or not.
    - other fields: the sampling parameters (See `SamplingParams` for details).
    """
    request_dict = await request.json()

    logger.warning(f'Received stop signal: {request_dict}')
    # os._exit(0)
    parent_pid = os.getpid()
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):  # or parent.children() for recursive=False
        child.kill()
    parent.kill()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--log-level", type=str, default="info")

    parser.add_argument("--mathlib_root", type=str)
    parser.add_argument("--eval_set", type=str)
    parser.add_argument("--working_root", type=str)
    parser.add_argument("--dataset_root", type=str)
    parser.add_argument("--repl_root", type=str)
    parser.add_argument("--try_num", type=int, default=8)
    parser.add_argument("--num_concurrency", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=None)

    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    os.makedirs(args.working_root, exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, level=('INFO' if args.num_concurrency > 1 else 'DEBUG'), enqueue=True)
    logger.add(osp.join(args.working_root, 'equivalence_qwen_server.log'), level='INFO', enqueue=True)
    logger.info(f'Server hyperparams: {args}')

    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine_args.disable_log_requests = True
    engine_args.enable_prefix_caching = True
    engine = AsyncLLMEngine.from_engine_args(
        engine_args, usage_context=UsageContext.API_SERVER)
    
    url = f'http://0.0.0.0:{args.port}'
    async_generate = async_generate_vllm
    logger.critical(f'Using local vllm server {args.model} @ {args.try_num} at T={args.temperature}')

    p = mp.Process(target=main, kwargs=dict(
        async_generate=async_generate,
        model_path=args.model,
        mathlib_root=args.mathlib_root,
        eval_set=args.eval_set,
        working_root=args.working_root,
        dataset_root=args.dataset_root,
        repl_root=args.repl_root,
        url=url,
        try_num=args.try_num,
        num_concurrency=args.num_concurrency,
        temperature=args.temperature,
    ))

    p.start()

    uvicorn.run(app,
                port=args.port,
                log_level=args.log_level,
                timeout_keep_alive=TIMEOUT_KEEP_ALIVE)
