import os
import json
import toml
import gc
import tqdm
import sys
import tomllib
from pathlib import Path

from typing import Any, Dict
from datasets.nestful.src.utils import read_jsonlines, write_jsonlines, read_json
from datasets.nestful.src.instruct_data_prep import (
    get_icl_str, 
    granite_prompt_input, 
    granite_3_1_prompt_input, 
    deepseek_prompt_input, 
)

from langchain_ollama.llms import OllamaLLM
from BenchmarkAdapter import BenchmarkAdapter

class NestfulAdapter(BenchmarkAdapter):
    
    def __init__(self, model_instance=None, memory_instance=None, benchmark_config=None, cfg_path=None):
        """
        Initialize NestfulAdapter for orchestrator integration.
        
        Args:
            model_instance: Model instance from orchestrator (preferred)
            memory_instance: Memory method instance from orchestrator (preferred)  
            benchmark_config: Benchmark configuration from orchestrator (preferred)
            cfg_path: Legacy config file path (for backward compatibility)
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels from evaluation/nestful to project root, then apply dataset path
        self.project_root = Path(self.base_dir).parent.parent
        self.nestful_dir = self.project_root / "datasets" / "nestful"
        
        # Handle orchestrator mode vs legacy mode
        if model_instance is not None and benchmark_config is not None:
            # Orchestrator mode - use passed instances and config
            self.model_instance = model_instance
            self.memory_instance = memory_instance
            self.cfg = benchmark_config
            self.orchestrator_mode = True
            
            # Set up supported models from config
            supported_models = self.cfg.get("supported_models", {})
            self.GRANITE_MODELS = supported_models.get("GRANITE_MODELS", [])
            self.GRANITE_3_1_MODELS = supported_models.get("GRANITE_3_1_MODELS", [])
            self.LLAMA_MODELS = supported_models.get("LLAMA_MODELS", [])
            self.DEEPSEEK = supported_models.get("DEEPSEEK", [])
            self.supported_models = supported_models
            
        else:
            # Legacy mode - load from config file
            if cfg_path is None:
                cfg_path = "config.toml"
            config_path = os.path.join(os.path.dirname(__file__), cfg_path)
            full_config = toml.load(config_path)
            cfg = full_config.get("nestful")
            if cfg is None:
                raise ValueError("Invalid config file")
            self.cfg = cfg
            self.model_instance = None
            self.memory_instance = None
            self.orchestrator_mode = False
            
            # Set up supported models from config
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

        icl_examples_list = read_json(self.nestful_dir / self.cfg["icl_examples_path"])
        icl_examples = icl_examples_list[:icl_ex_count]
        prompt_dict = read_json(self.nestful_dir / self.cfg["prompts_path"])

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
        # Go up two levels from evaluation/nestful to project root, then apply dataset path
        dataset_path = self.nestful_dir / self.cfg["dataset"]

        data = read_jsonlines(dataset_path)
        
        # Handle demo mode - select only one random task
        if self.cfg.get("demo", False):
            import random
            data = [random.choice(data)]
            sample_id = data[0].get('sample_id', 'unknown') if isinstance(data[0], dict) else 'unknown'
            print(f"### Demo mode: Running with 1 random task (ID: {sample_id})")
        
        # Get model name for prompt processing
        if self.orchestrator_mode and self.model_instance is not None:
            model_info = self.model_instance.get_model_info()
            model_name = model_info.get("name", "unknown") if isinstance(model_info, dict) else "unknown"
        else:
            model_name = self.cfg.get("model_name", "unknown")
            
        instruct_data = self._get_instruct_data(
            data,
            "orchestrator" if self.orchestrator_mode else self.cfg["provider"],
            model_name,
            self.cfg["icl_count"],
            data_limit=None if self.cfg.get("demo", False) else self.cfg.get("data_limit")
        )

        print("### Starting Generation...")
        response, output_list = [], []
        batch_size = self.cfg["batch_size"]
        count_total_batches = -(-len(instruct_data) // batch_size) 

        if self.orchestrator_mode and self.model_instance is not None:
            # Use orchestrator's model instance
            for idx in range(0, len(instruct_data), batch_size):
                print(f"### At batch {idx // batch_size + 1} out of {count_total_batches} batches...")
                batch_data = instruct_data[idx: idx + batch_size]

                for sample in batch_data:
                    try:
                        # Apply memory processing if available
                        processed_prompt = sample["input"]
                        if self.memory_instance:
                            processed_prompt = self.memory_instance.process(processed_prompt)
                        
                        # Generate response using orchestrator's model
                        response_data = await self.model_instance.generate_text(
                            prompt=processed_prompt,
                            system="You are a helpful AI assistant.",
                            temperature=self.cfg.get("temperature", 0.0),
                            max_tokens=self.cfg.get("max_tokens", 1000)
                        )
                        
                        # Extract content from response
                        content = response_data.get("message", {}).get("content", "")
                        response.append(content.strip())
                        
                    except Exception as e:
                        print(f"Error generating for prompt: {e}")
                        response.append("")
        else:
            # Legacy mode - use direct Ollama LLM
            print("### Loading Model...")
            llm = OllamaLLM(
                model=model_name,
                temperature=self.cfg["temperature"],
                num_predict=self.cfg["max_tokens"],
            )

            for idx in range(0, len(instruct_data), batch_size):
                print(f"### At batch {idx // batch_size + 1} out of {count_total_batches} batches...")
                batch_data = instruct_data[idx: idx + batch_size]

                for sample in batch_data:
                    try:
                        output = llm.invoke(sample["input"])
                        response.append(output.strip())
                    except Exception as e:
                        print(f"Error generating for prompt: {e}")
                        response.append("")

            # Clean up
            del llm
            gc.collect()

        # Combine responses with instruct data
        for idx in range(len(response)):
            temp = instruct_data[idx]
            temp["generated_text"] = response[idx]
            output_list.append(temp)

        # Save results if not in demo mode
        if not self.cfg.get("demo", False):
            icl_count = self.cfg["icl_count"]
            save_path = os.path.join(
                self.base_dir,
                "..",
                self.cfg["save_directory"],
                f"nestful_{icl_count}",
                model_name,
                "output.jsonl"
            )
            print(f"### Save Path: {save_path}")
            os.makedirs(os.path.join(self.base_dir, "..", self.cfg["save_directory"], f"nestful_{icl_count}", model_name), exist_ok=True)
            write_jsonlines(output_list, save_path)

        print("### DONE...!!!")

        # Format output_list to match expected return type Dict[str, Any]
        results = {
            "models": {
                model_name: {
                    "tasks": output_list
                }
            },
            "metadata": {
                "timestamp": None,
                "config": self.cfg,
                "aggregate_metrics": None,
                "demo_mode": self.cfg.get("demo", False)
            }
        }
        return results
    
    def evaluate_result(self, task=None, execution_result=None):
        # can be implemented using the nestful/src/scorer.py file
        pass
