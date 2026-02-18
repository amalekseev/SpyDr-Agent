from pathlib import Path

from omegaconf import OmegaConf

global_config = OmegaConf.load(Path(__file__).parent / "config.yml")
