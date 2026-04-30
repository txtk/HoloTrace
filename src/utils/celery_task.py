from CeleryManage.scheduler import celery_app
import poml
from utils.llm_use import add_total_tokens, get_embedding, get_response_poml, get_total_tokens, reset_total_tokens
from celery import signature, chain
from typing import List, Union

def run_celery(celery_task_name: str, args_list):
    task_to_run = []
    for args in args_list:
        task = celery_app.send_task(celery_task_name, args=args)
        task_to_run.append(task)
    return task_to_run

@celery_app.task(name="task.completion", ignore_result=False)
def completion(context, prompt_path):
    prompt = poml.poml(prompt_path, context=context, format="openai_chat")
    result = get_response_poml(prompt)
    return result


@celery_app.task(name="task.completion_with_usage", ignore_result=False)
def completion_with_usage(context, prompt_path):
    reset_total_tokens()
    prompt = poml.poml(prompt_path, context=context, format="openai_chat")
    result = get_response_poml(prompt)
    used_tokens = get_total_tokens()
    return {"result": result, "tokens": used_tokens}

@celery_app.task(name="task.embedding", ignore_result=False)
def embedding(content: Union[str, List[str]], dimensions):
    result = get_embedding(content, dimensions)
    return result


def get_completion_result_single(context, prompt_path):
    task = celery_app.send_task(
        "task.completion",
        args=(context, prompt_path),
    )
    result = task.get()
    return result


def get_completion_result_batch(contexts, prompt_path):
    args_list = [(context, prompt_path) for context in contexts]
    tasks = run_celery("task.completion", args_list)
    results = [task.get() for task in tasks]
    return results


def get_completion_result_batch_with_usage(contexts, prompt_path):
    args_list = [(context, prompt_path) for context in contexts]
    tasks = run_celery("task.completion_with_usage", args_list)

    results = []
    total_tokens = 0
    for task in tasks:
        payload = task.get()
        if isinstance(payload, dict):
            results.append(payload.get("result"))
            total_tokens += int(payload.get("tokens", 0) or 0)
        else:
            results.append(payload)

    add_total_tokens(total_tokens)
    return results


def make_chain_celery_single(celery_task_names: str, args):
    first = True
    tasks = []
    for celery_task_name in celery_task_names:
        if first:
            first = False
            task = signature(celery_task_name, args=args)
        else:
            task = signature(celery_task_name)
        tasks.append(task)
    workflow = chain(*tasks)
    result = workflow.apply_async()
    return result
        
def get_embedding_celery(content: Union[str, List[str]], dimensions: int = 1024):
    task = celery_app.send_task(
        "task.embedding",
        args=(content, dimensions),
    )
    result = task.get()
    return result