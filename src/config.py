"""
Configuration management for the AI red-teaming tool.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration loading from various sources."""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Find project root by looking for requirements.txt
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "requirements.txt").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                raise RuntimeError("Could not find project root")
        
        self.project_root = project_root
        self.config_dir = project_root / "config"
        self.local_dir = project_root / "local"
        
        # Ensure local directory exists
        self.local_dir.mkdir(exist_ok=True)
    
    def load_datasets_config(self) -> Dict[str, Any]:
        """Load dataset configurations."""
        config_path = self.config_dir / "datasets.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_target_api_config(self) -> Dict[str, Any]:
        """Load target API configuration from local directory."""
        config_path = self.local_dir / "target_api.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Target API config not found at {config_path}. "
                f"Copy config/target_api_template.yaml to local/target_api.yaml "
                f"and configure it for your API."
            )
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load system context if specified
        if 'system_context_file' in config:
            context_file = self.local_dir / config['system_context_file']
            if context_file.exists():
                with open(context_file, 'r') as f:
                    config['system_context'] = f.read().strip()
            else:
                print(f"Warning: System context file {context_file} not found")
                config['system_context'] = "Generic AI assistant"
        
        return config
    
    def get_dataset_config(self, dataset_name: str) -> Dict[str, Any]:
        """Get configuration for a specific dataset."""
        datasets = self.load_datasets_config()
        if dataset_name not in datasets['datasets']:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        return datasets['datasets'][dataset_name]
    
    def list_available_datasets(self) -> list[str]:
        """List all configured datasets."""
        datasets = self.load_datasets_config()
        return list(datasets['datasets'].keys())
    
    def validate_environment(self) -> bool:
        """Validate that required environment variables are set."""
        required_vars = ['CLAUDE_API_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"Missing required environment variables: {', '.join(missing)}")
            return False
        
        return True
    
    def create_local_config_template(self):
        """Create example local configuration files."""
        # Create target_api.yaml if it doesn't exist
        target_config = self.local_dir / "target_api.yaml"
        if not target_config.exists():
            template_path = self.config_dir / "target_api_template.yaml"
            with open(template_path, 'r') as f:
                template = f.read()
            
            with open(target_config, 'w') as f:
                f.write(template)
            
            print(f"Created template config at {target_config}")
        
        # Create system_context.txt if it doesn't exist
        context_file = self.local_dir / "system_context.txt"
        if not context_file.exists():
            default_context = (
                "This is a helpful AI assistant that provides information "
                "and assistance to users on a wide range of topics."
            )
            with open(context_file, 'w') as f:
                f.write(default_context)
            
            print(f"Created template system context at {context_file}")


# Global config manager instance
config_manager = ConfigManager()
