import os
import json
import toml
import sys
import gc

# Add the nestful src directory to path for proper imports
base_dir = os.path.dirname(os.path.abspath(__file__))
nestful_src_path = os.path.join(base_dir, "..", "datasets", "nestful", "src")
sys.path.insert(0, nestful_src_path)

from utils import read_jsonlines, write_jsonlines
from langchain_ollama.llms import OllamaLLM
from instruct_data_prep import get_instruct_data


def eval_code(cfg):
    print("### Loading Data...")

    # Construct absolute path relative to the evaluation directory
    dataset_path = os.path.join(base_dir, "..", cfg["dataset"])
    data = read_jsonlines(dataset_path)

    for i in range(len(data)):
        data[i]["tools"] = json.dumps(data[i]["tools"])
        data[i]["gold_answer"] = json.dumps(data[i]["gold_answer"])
        data[i]["output"] = json.dumps(data[i]["output"])

    print("### Preparing Instruct Data...")
    instruct_data = get_instruct_data(
        data,
        cfg["model"],
        cfg["model_name"],
        cfg["icl_count"],
        data_limit=cfg.get("data_limit")
    )

    print("### Loading Model...")

    llm = OllamaLLM(
        model=cfg["model_name"],
        temperature=cfg["temperature"],
        num_predict=cfg["max_tokens"],
    )

    prompts = [sample["input"] for sample in instruct_data]

    print("### Starting Generation...")
    response, output_list = [], []
    batch_size = cfg["batch_size"]
    count_total_batches = -(-len(prompts) // batch_size) 

    for idx in range(0, len(prompts), batch_size):
        print(f"### At batch {idx // batch_size + 1} out of {count_total_batches} batches...")
        prompt_batch = prompts[idx: idx + batch_size]

        for prompt in prompt_batch:
            try:
                output = llm.invoke(prompt)
                response.append(output.strip())
            except Exception as e:
                print(f"Error generating for prompt: {e}")
                response.append("")

    for idx in range(len(response)):
        temp = instruct_data[idx]
        temp["generated_text"] = response[idx]
        output_list.append(temp)

    # Clean up
    del llm
    gc.collect()

    icl_count = cfg["icl_count"]

    print("### Saving...")
    save_path = os.path.join(
        base_dir,
        "..",
        cfg["save_directory"],
        f"nestful_{icl_count}",
        cfg["model_name"],
        "output.jsonl"
    )
    print(f"### Save Path: {save_path}")
    os.makedirs(os.path.join(base_dir, "..", cfg["save_directory"], f"nestful_{icl_count}", cfg["model_name"]), exist_ok=True)
    write_jsonlines(output_list, save_path)

    print("### DONE...!!!")

if __name__ == "__main__":
    # Read config from TOML file
    config_path = os.path.join(os.path.dirname(__file__), "config.toml")
    full_config = toml.load(config_path)
    cfg = full_config.get("nestful")

    print("Configuration:")
    for key, value in cfg.items():
        print(f"{key}: {value}")

    eval_code(cfg)