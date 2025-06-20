"""
Dataset adapters for normalizing different dataset formats.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, List
import pandas as pd
from datasets import load_dataset


class DatasetAdapter(ABC):
    """Base class for dataset adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config['name']
        self.description = config.get('description', '')
    
    @abstractmethod
    def load_prompts(self, limit: int = None) -> Iterator[Dict[str, Any]]:
        """
        Load prompts from the dataset.
        
        Returns:
            Iterator of dicts with keys: 'prompt', 'label', 'source', 'metadata'
        """
        pass
    
    def normalize_label(self, original_label: Any) -> str:
        """Normalize label to 'benign' or 'malicious'."""
        label_mapping = self.config.get('label_mapping', {})
        label_all_as = self.config.get('label_all_as')
        
        if label_all_as:
            return label_all_as
        
        if label_mapping and original_label in label_mapping:
            return label_mapping[original_label]
        
        return str(original_label)


class SimpleDatasetAdapter(DatasetAdapter):
    """Adapter for simple CSV/Parquet datasets with prompt and label columns."""
    
    def load_prompts(self, limit: int = None) -> Iterator[Dict[str, Any]]:
        try:
            # Load from HuggingFace - try common split names
            dataset = None
            for split_name in ['train', 'test', 'validation']:
                try:
                    dataset = load_dataset(self.name, split=split_name)
                    print(f"Loaded dataset {self.name} using '{split_name}' split")
                    break
                except Exception:
                    continue
            
            if dataset is None:
                # If no common splits work, try loading without specifying split
                dataset_info = load_dataset(self.name)
                available_splits = list(dataset_info.keys())
                if available_splits:
                    split_name = available_splits[0]
                    dataset = dataset_info[split_name]
                    print(f"Loaded dataset {self.name} using '{split_name}' split")
                else:
                    raise ValueError(f"No accessible splits found for {self.name}")
            
            if limit:
                dataset = dataset.select(range(min(limit, len(dataset))))
            
            columns = self.config['columns']
            prompt_col = columns['prompt']
            label_col = columns.get('label')
            
            for row in dataset:
                prompt = row[prompt_col]
                if not prompt or not isinstance(prompt, str):
                    continue
                
                original_label = row.get(label_col) if label_col else None
                normalized_label = self.normalize_label(original_label)
                
                yield {
                    'prompt': prompt.strip(),
                    'label': normalized_label,
                    'source': self.name,
                    'metadata': {
                        'original_label': original_label,
                        'row_data': row
                    }
                }
                
        except Exception as e:
            print(f"Error loading dataset {self.name}: {e}")
            return


class XXZ224Adapter(DatasetAdapter):
    """Adapter for xxz224 multi-attack dataset."""
    
    def load_prompts(self, limit: int = None) -> Iterator[Dict[str, Any]]:
        try:
            # Load from HuggingFace - try common split names
            dataset = None
            for split_name in ['train', 'test', 'validation']:
                try:
                    dataset = load_dataset(self.name, split=split_name)
                    print(f"Loaded dataset {self.name} using '{split_name}' split")
                    break
                except Exception:
                    continue
            
            if dataset is None:
                # If no common splits work, try loading without specifying split
                dataset_info = load_dataset(self.name)
                available_splits = list(dataset_info.keys())
                if available_splits:
                    split_name = available_splits[0]
                    dataset = dataset_info[split_name]
                    print(f"Loaded dataset {self.name} using '{split_name}' split")
                else:
                    raise ValueError(f"No accessible splits found for {self.name}")
            
            if limit:
                # Since we extract multiple prompts per row, limit the rows
                row_limit = max(1, limit // len(self.config['attack_columns']))
                dataset = dataset.select(range(min(row_limit, len(dataset))))
            
            attack_columns = self.config['attack_columns']
            count = 0
            
            for row in dataset:
                if limit and count >= limit:
                    break
                    
                # Extract attack prompts from each attack column
                for attack_type in attack_columns:
                    if attack_type in row and row[attack_type]:
                        attack_prompt = row[attack_type]
                        if isinstance(attack_prompt, str) and attack_prompt.strip():
                            yield {
                                'prompt': attack_prompt.strip(),
                                'label': 'malicious',
                                'source': f"{self.name}_{attack_type}",
                                'metadata': {
                                    'attack_type': attack_type,
                                    'target_text': row.get('target_text', ''),
                                    'row_id': row.get('id', count)
                                }
                            }
                            count += 1
                            if limit and count >= limit:
                                break
                                
        except Exception as e:
            print(f"Error loading dataset {self.name}: {e}")
            return


def create_adapter(dataset_name: str, config: Dict[str, Any]) -> DatasetAdapter:
    """Factory function to create appropriate adapter."""
    if dataset_name == 'xxz224':
        return XXZ224Adapter(config)
    else:
        return SimpleDatasetAdapter(config)
