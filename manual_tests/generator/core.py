import os
import glob
from typing import List, Optional
from openai import OpenAI
from .config import config

class FeatureParser:
    @staticmethod
    def read_feature_file(file_path: str) -> str:
        """Reads the content of a feature file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

class LLMClient:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
        else:
            print("Warning: OPENAI_API_KEY not set. LLM generation will be skipped.")

    def generate_human_test(self, gherkin_content: str) -> Optional[str]:
        """Generates a human-readable test description from Gherkin content."""
        if not self.client:
            return None

        prompt = config.PROMPT_TEMPLATE.format(gherkin_content=gherkin_content)

        try:
            response = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating test with LLM: {e}")
            return None

class Generator:
    def __init__(self, features_dir: str, output_dir: str):
        self.features_dir = features_dir
        self.output_dir = output_dir
        self.llm_client = LLMClient()

    def run(self):
        """Runs the generation process for all feature files."""
        feature_files = glob.glob(os.path.join(self.features_dir, "*.feature"))
        
        if not feature_files:
            print(f"No feature files found in {self.features_dir}")
            return

        print(f"Found {len(feature_files)} feature files.")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for file_path in feature_files:
            filename = os.path.basename(file_path)
            print(f"Processing {filename}...")
            
            gherkin_content = FeatureParser.read_feature_file(file_path)
            if not gherkin_content:
                continue

            # Generate multiple versions if configured (though simple implementation does 1 loop for now based on plan structure, 
            # but config has GENERATIONS_PER_FEATURE. Let's support that simply)
            for i in range(config.GENERATIONS_PER_FEATURE):
                human_test_content = self.llm_client.generate_human_test(gherkin_content)
                
                if human_test_content:
                    base_name = os.path.splitext(filename)[0]
                    suffix = f"_{i+1}" if config.GENERATIONS_PER_FEATURE > 1 else ""
                    output_filename = f"{base_name}{suffix}.txt"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    self._save_file(output_path, human_test_content)
                    print(f"  Saved to {output_filename}")
                else:
                    print(f"  Skipped generation for {filename} (LLM error or no key)")

    def _save_file(self, path: str, content: str):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving file {path}: {e}")
