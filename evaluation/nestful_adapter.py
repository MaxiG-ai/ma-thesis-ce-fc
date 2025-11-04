import os
import json
import toml
import gc
import tqdm
import sys
import tomllib
from pathlib import Path

from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_ollama.llms import OllamaLLM
from datasets.nestful.src.utils import (read_jsonlines, write_jsonlines, read_json)

from datasets.nestful.src.instruct_data_prep import (
    get_icl_str, 
    granite_prompt_input, 
    granite_3_1_prompt_input, 
    deepseek_prompt_input, 
    )

from BenchmarkAdapter import BenchmarkAdapter

class NestfulAdapter(BenchmarkAdapter):
    
    def __init__(self, cfg_path):
        config_path = os.path.join(os.path.dirname(__file__), cfg_path)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.nestful_dir = os.path.join(self.base_dir, "..", "datasets", "nestful")
        full_config = toml.load(config_path)
        cfg = full_config.get("nestful")
        if cfg is None:
            raise ValueError("Invalid config file")
        self.cfg = cfg
        self.supported_models = cfg["supported_models"]
        self.GRANITE_MODELS = self.supported_models["GRANITE_MODELS"]
        self.GRANITE_3_1_MODELS = self.supported_models["GRANITE_3_1_MODELS"]
        self.LLAMA_MODELS = self.supported_models["LLAMA_MODELS"]
        self.DEEPSEEK = self.supported_models["DEEPSEEK"]

    @classmethod
    def load_config_from_file(
        cls,
        config_path: str,
        section: str = "nestful"
    ) -> Dict[str, Any]:
        """
        Load configuration from a TOML file.
        
        Args:
            config_path: Path to the TOML configuration file
            section: Section name in the TOML file (default: "mcpbench")
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If section is not found in config
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, "rb") as f:
            full_config = tomllib.load(f)
        
        if section not in full_config:
            raise ValueError(
                f"Section '{section}' not found in config file. "
                f"Available sections: {', '.join(full_config.keys())}"
            )
        
        return full_config[section]


    def _get_instruct_data(self, data, model, model_name, icl_ex_count=3, data_limit=None):
        if data_limit is not None:
            data = data[:data_limit]

        icl_examples_list = read_json(self.nestful_dir + '/src/icl_examples.json')
        icl_examples = icl_examples_list[:icl_ex_count]
        prompt_dict = read_json(self.nestful_dir + '/src/PROMPTS.json')

        test_data = []
        icl_str = get_icl_str(icl_examples, model_name)
        for sample in tqdm.tqdm(data):
            if model_name in self.GRANITE_MODELS:
                input_prompt = granite_prompt_input(sample['input'], sample['tools'], icl_str)
            elif model_name in self.GRANITE_3_1_MODELS:
                input_prompt = granite_3_1_prompt_input(sample['input'], json.loads(sample['tools']), icl_str, model)
            elif model_name in self.LLAMA_MODELS:
                input_prompt = prompt_dict["LLaMa-3.1"].format(FUNCTION_STR=json.dumps(sample['tools']), ICL_EXAMPLES=icl_str, QUERY=sample['input'])
            elif model_name in self.DEEPSEEK:
                input_prompt = deepseek_prompt_input(sample['input'], sample["tools"], icl_str)
            else:
                try:
                    input_prompt = prompt_dict[model_name].format(FUNCTION_STR=json.dumps(sample['tools']), ICL_EXAMPLES=icl_str, QUERY=sample['input'])
                except KeyError:
                    input_prompt = prompt_dict[model_name].replace('{FUNCTION_STR}', json.dumps(sample['tools'])).replace("{ICL_EXAMPLES}", icl_str).replace('{QUERY}', sample['input'])
            test_data.append(
                {
                    "sample_id": sample['sample_id'],
                    "input": input_prompt,
                    "output": sample['output'],
                    "gold_answer": sample['gold_answer'],
                    "tools": sample["tools"] ## keeping for scoring
                }
            )
        return test_data

    async def run_benchmark(self, selected_models=None, task_limit=None) -> Dict[str, Any]:
        print("### Loading Data...")

        # Construct absolute path relative to the evaluation directory
        dataset_path = os.path.join(
            self.base_dir , "..", self.cfg["dataset"]
        )
        data = read_jsonlines(dataset_path)
        instruct_data = self._get_instruct_data(
            data,
            self.cfg["provider"],
            self.cfg["model_name"],
            self.cfg["icl_count"],
            data_limit=self.cfg.get("data_limit")
        )

        print("### Loading Model...")

        llm = OllamaLLM(
            model=self.cfg["model_name"],
            temperature=self.cfg["temperature"],
            num_predict=self.cfg["max_tokens"],
        )

        prompts = [sample["input"] for sample in instruct_data]

        print("### Starting Generation...")
        response, output_list = [], []
        batch_size = self.cfg["batch_size"]
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

        # TODO: write results to file in separate function
        icl_count = self.cfg["icl_count"]

        print("### Saving...")
        save_path = os.path.join(
            self.base_dir,
            "..",
            self.cfg["save_directory"],
            f"nestful_{icl_count}",
            self.cfg["model_name"],
            "output.jsonl"
        )
        print(f"### Save Path: {save_path}")
        os.makedirs(os.path.join(self.base_dir, "..", self.cfg["save_directory"], f"nestful_{icl_count}", self.cfg["model_name"]), exist_ok=True)
        write_jsonlines(output_list, save_path)

        print("### DONE...!!!")

        # format output_list to match expected return type Dict[str, Any]
        results = {
            "models": {
                self.cfg["model_name"]: {
                    "tasks": output_list
                }
            },
            "metadata": {
                "timestamp": None,
                "config": self.cfg,
                "aggregate_metrics": None
            }
        }
        return results
    
    def evaluate_result(self, task=None, execution_result=None):
        # can be implemented using the nestful/src/scorer.py file
        pass