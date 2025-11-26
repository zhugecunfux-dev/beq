#!/bin/bash
# 启动监控
(while true; do
    date
    free -h
    nvidia-smi --query-gpu=memory.used,memory.free --format=csv
    echo "---"
    sleep 5
done) > memory_log.txt 2>&1 &
MONITOR_PID=$!

export BEQ_LEVEL=basic   
export EQ_BENCHMARK=o1-generated 
mkdir -p ./mnt/disk0/t00917290/result && \
cp ./data/human_equivalence/${EQ_BENCHMARK}/autoformalization.jsonl /mnt/disk0/t00917290/result && \
python -m equivalence.beq_${BEQ_LEVEL} \
    --equiv_url http://localhost:13420/v1 \
    --trust-remote-code \
    --enable-prefix-caching \
    --equiv_model kimina_72b\
    --mathlib_root /mnt/disk0/t00917290/imo_autoformalization/rethinking_autoformalization/mathlib4 \
    --eval_set proofnet \
    --working_root /mnt/disk0/t00917290/result \
    --dataset_root ./data/ \
    --repl_root /mnt/disk0/t00917290/imo_autoformalization/rethinking_autoformalization/repl \
    --try_num 16 \
    --num_concurrency 1 \
    --temperature 0.0

# 停止监控
kill $MONITOR_PID

# 查看内存使用峰值
cat memory_log.txt
