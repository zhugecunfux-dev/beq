# 兼容 vLLM 不同版本的工具函数
try:
    from vllm.utils import random_uuid as _random_uuid
except Exception:
    _random_uuid = None

try:
    from vllm.utils import iterate_with_cancellation as _iterate
except Exception:
    _iterate = None

# 始终导出 random_uuid
if _random_uuid is not None:
    random_uuid = _random_uuid
else:
    import uuid
    def random_uuid() -> str:
        return str(uuid.uuid4())

# 始终导出 iterate_with_cancellation
if _iterate is not None:
    iterate_with_cancellation = _iterate
else:
    # 简化降级版：忽略“取消”语义，直接把 async 迭代器透传
    async def iterate_with_cancellation(aiter, *args, **kwargs):
        async for x in aiter:
            yield x
