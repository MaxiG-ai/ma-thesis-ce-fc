python -u datasets/nestful/src/eval.py \
    --model "llama3.1:8b" \
    --model_name "llama3.1:8b" \
    --save_directory "results" \
    --dataset "datasets/nestful/data_v2/nestful_data.jsonl" \
    --icl_count 3 \
    --temperature 0 \
    --max_tokens 1000 \
    --batch_size 1                                               # Number of in-context examples to use (e.g., 3)