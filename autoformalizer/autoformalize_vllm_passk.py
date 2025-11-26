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
import fire
from easydict import EasyDict
from openai import OpenAI, AsyncOpenAI
from tqdm import tqdm
from xtuner.utils import PROMPT_TEMPLATE
from xtuner.dataset.map_fns import template_map_fn_factory
from loguru import logger

from common.constants import INIT_WAIT_TIME
from common.dataclasses import Environment
from common.repl import REPL


TIMEOUT_KEEP_ALIVE = 5  # seconds.
app = FastAPI()
engine = None

default_template_map = template_map_fn_factory(PROMPT_TEMPLATE.default)
THM_CODE_PATTERN = re.compile(r'theorem (.*?)sorry', flags=re.DOTALL)

def unique(r : list) -> list:
    s = []
    for i in r:
        if i not in s:
            s.append(i)
    return s

def format_prompt(informal_stmt: str) -> str:
    return f'''Statement in natural language:
{informal_stmt}
Translate the statement in natural language to Lean:'''


async def async_generate(input_prompt, url, sampling_params: Dict):
    final_output = None
    prompt = default_template_map({
        "conversation":[
            {
                "system": "You are an expert on Lean 4 and Isabelle.",
                "input": input_prompt,
            }
        ]
    })['conversation'][0]['input']
    
    async with aiohttp.ClientSession() as session:
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
        mathlib_root: str,
        eval_set: str,
        working_root: str,
        dataset_root: str,
        repl_root: str,
        url: str,
        try_num: int=1,
        early_exit: bool=False,
        num_concurrency: int=16,
        max_tokens: int=512,
        temperature: Optional[float]=None
        ):
    if temperature is None:
        temperature = 0.0 if try_num == 1 else 0.7
    
    saved_args = {**locals()}
    os.makedirs(working_root, exist_ok=True)
    logger.add(osp.join(working_root, 'autoformalization.log'))
    logger.info(f'hyperparameters: {saved_args}')

    with open(osp.join(dataset_root, eval_set, 'library.jsonl'), 'r') as f:
        premises_with_informalization = [json.loads(l) for l in f.readlines()]
    premises_dict = {p['full_name'] : p for p in premises_with_informalization}

    samples = []
    with open(osp.join(dataset_root, eval_set, 'benchmark.jsonl'), 'r') as f:
        for line in f.readlines():
            samples.append(json.loads(line))
    # ['informal_stmt', 'formal_stmt', 'header', 'proof_state', 'mathlib_dependencies', 'hard_dependencies', 'source', 'problem_name']

    loop = asyncio.get_event_loop()

    try:
        # Prepare result recording
        autoformalization_result = C.defaultdict(lambda : list())
        if osp.exists(osp.join(working_root, f'autoformalization.json')) and osp.isfile(osp.join(working_root, f'autoformalization.json')):
            logger.info(f'Loading autoformalization result from {osp.join(working_root, "autoformalization.json")}...')
            with open(osp.join(working_root, f'autoformalization.json'), 'r') as f:
                for k, sample in json.load(f).items():
                    autoformalization_result[k] = sample
        else:
            logger.info(f'Running autoformalization for all items...')

        async def autoformalize(sample: Dict):
            # sample: ['informal_stmt', 'formal_stmt', 'header', 'proof_state', 'mathlib_dependencies', 'hard_dependencies', 'source', 'problem_name']
            logger.debug(f'Autoformalize(): Running on {sample}')
            class_name, problem_name = sample['source'], sample['problem_name']
            formal_stmt_gt = sample['formal_stmt']
            # Construct autoformalization prompt
            input_prompt = format_prompt(sample['informal_stmt'])
            logger.debug(f'Autoformalize({class_name}.{problem_name}): Input prompt: {[input_prompt]}')
            logger.debug(f'Autoformalize({class_name}.{problem_name}): Ground-truth: {formal_stmt_gt}')

            repl = REPL(
                repl_root=repl_root,
                project_root=mathlib_root,
            )
            repl._run_interactive()
            await asyncio.sleep(INIT_WAIT_TIME)
            init_env = await repl.run_cmd_async(sample['header'])
            logger.debug(f'Autoformalize({class_name}.{problem_name}): REPL Initialize finished.')

            if temperature == 0.0 and try_num > 1:  # Use beam search
                final_output = await async_generate(
                    input_prompt=input_prompt,
                    url=url+'/generate',
                    sampling_params=dict(
                        n=try_num,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        use_beam_search=True
                    )
                )
                outputs = final_output.outputs
            else:
                outputs = []
                for _ in range(try_num):
                    try:
                        final_output = await async_generate(
                            input_prompt=input_prompt,
                            url=url+'/generate',
                            sampling_params=dict(
                                max_tokens=max_tokens,
                                temperature=temperature,
                            )
                        )
                        assert len(final_output.outputs) == 1
                        outputs.append(final_output.outputs[0])
                    except Exception as e:
                        logger.warning(f'Autoformalize({class_name}.{problem_name}): Model inference error: {e}, {[traceback.format_exc()]}')


            if len(outputs) != try_num:
                logger.warning(f'Autoformalize({class_name}.{problem_name}): Got {len(outputs)} autoformalizations but {try_num} expected.')

            for try_i, output in enumerate(outputs):
                try:
                    # Autoformalize
                    cur_result = dict()
                    formal_stmt_pred = output.text
                    if 'sorry' not in formal_stmt_pred:
                        formal_stmt_pred += '\nsorry'
                    formal_stmt_gt = formal_stmt_gt.replace(f'theorem {problem_name}', 'theorem thm_P')
                    logger.debug(f'Autoformalize({class_name}.{problem_name}, {try_i}): Autoformalization: {formal_stmt_pred}')

                    matches_thm = list(re.finditer(THM_CODE_PATTERN, formal_stmt_pred))
                    matches_eg = list(re.finditer('example', formal_stmt_pred))
                    if len(matches_thm) == 1:
                        thm_name = matches_thm[0].group().split()[1].strip()
                        formal_stmt_pred = formal_stmt_pred.replace(f'theorem {thm_name}', 'theorem thm_Q')
                    elif len(matches_eg) == 1:
                        formal_stmt_pred = formal_stmt_pred.replace(f'example', 'theorem thm_Q')
                    else:
                        raise RuntimeError('Unable to parse formal_stmt_pred')

                    cur_result['formal_stmt_pred'] = formal_stmt_pred

                    # Typecheck
                    run_result = None
                    is_success_typecheck = False
                    try:
                        run_result = await repl.run_cmd_async(formal_stmt_gt + '\n\n' + formal_stmt_pred + '\n', init_env)
                        assert 'error' not in str(run_result.messages)
                        is_success_typecheck = True
                    except Exception as e:
                        pass
                    
                    run_result = run_result.serialize() if run_result is not None else dict()
                    cur_result['typecheck_result'] = {
                        'is_success': is_success_typecheck,
                        'result': run_result
                    }
                    
                    if is_success_typecheck:
                        logger.debug(f'Autoformalize({class_name}.{problem_name}, {try_i}): type check succeeded.')
                    else:
                        logger.debug(f'Autoformalize({class_name}.{problem_name}, {try_i}): type check failed with {run_result}.')
                        raise RuntimeError('Type check failed')
                    
                    if is_success_typecheck and early_exit:
                        # Early exist at the first successful typechecked autoformalization
                        break
                except Exception as e:
                    logger.debug(f'Autoformalize({class_name}.{problem_name}, {try_i}): Failed with {e}')
                    pass
                finally:
                    autoformalization_result[sample['full_name']].append(cur_result)
            typecheck_successes = [r for r in autoformalization_result[sample['full_name']] if 'typecheck_result' in r.keys() and r['typecheck_result']['is_success']]
            PQ_successes = [i for i, r in enumerate(typecheck_successes) if 'equivcheck_results_PQ' in r.keys() and r['equivcheck_results_PQ']['is_success']]
            QP_successes = [i for i, r in enumerate(typecheck_successes) if 'equivcheck_results_QP' in r.keys() and r['equivcheck_results_QP']['is_success']]
            equiv_successes = set(PQ_successes).intersection(set(QP_successes))
            logger.info(f'Autoformalize({class_name}.{problem_name}): Success Count of (T, PQ, QP, Equiv): {len(typecheck_successes)} {len(PQ_successes)} {len(QP_successes)} {len(equiv_successes)}')

        async def _async_main():
            pending_tasks: Set[asyncio.Task] = set()
            for i, v in tqdm(enumerate(samples)):
                if v['full_name'] in autoformalization_result.keys():
                    continue
                if len(pending_tasks) >= num_concurrency:
                    done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                pending_tasks.add(
                    asyncio.create_task(
                        autoformalize(v)
                    )
                )
            if len(pending_tasks) > 0:
                await asyncio.wait(pending_tasks)
            await logger.complete()

        # asyncio.run(_async_main())
        loop.run_until_complete(_async_main())
    except Exception as e:
        logger.error(f'Fatal Error: {e}, {traceback.format_exc()}')
    finally:
        try:
            with open(osp.join(working_root, f'autoformalization.json'), 'w') as f:
                json.dump(autoformalization_result, f)
            response = requests.post(
                url=url+'/stop', json=saved_args
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
    parser.add_argument("--try_num", type=int, default=1)
    parser.add_argument("--early_exit", action='store_true')
    parser.add_argument("--num_concurrency", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=None)

    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    os.makedirs(args.working_root, exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, level=('INFO' if args.num_concurrency > 1 else 'DEBUG'))
    logger.add(osp.join(args.working_root, 'server.log'), level='INFO')
    logger.info(f'Server hyperparams: {args}')

    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine_args.disable_log_requests = True
    engine_args.enable_prefix_caching = True
    engine = AsyncLLMEngine.from_engine_args(
        engine_args, usage_context=UsageContext.API_SERVER)

    # os execute cmd
    url = f'http://0.0.0.0:{args.port}'

    p = mp.Process(target=main, kwargs=dict(
        mathlib_root=args.mathlib_root,
        eval_set=args.eval_set,
        working_root=args.working_root,
        dataset_root=args.dataset_root,
        repl_root=args.repl_root,
        url=url,
        try_num=args.try_num,
        early_exit=args.early_exit,
        num_concurrency=args.num_concurrency,
        temperature=args.temperature,
    ))

    p.start()

    uvicorn.run(
        app,
        port=args.port,
        log_level=args.log_level,
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE
    )
