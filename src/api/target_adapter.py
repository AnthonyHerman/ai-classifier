"""
Target API adapter for sending prompts to arbitrary APIs.
"""
import json
import uuid
import time
import random
import string
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from copy import deepcopy


class TargetAPIAdapter:
    """Adapter for sending prompts to target APIs with flexible request templates."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_config = config['api']
        self.request_template = config['request_template']
        self.response_extraction = config['response_extraction']
        self.settings = config.get('settings', {})
        self._counter = 0
    
    async def send_prompt(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to the target API and extract the response.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Extracted response text or None if failed
        """
        try:
            # Build the request
            request_data = self._build_request(prompt)
            
            # Send the request
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(
                    total=self.settings.get('timeout', 30)
                )
                
                async with session.request(
                    method=self.api_config.get('method', 'POST'),
                    url=self.api_config['url'] + self.api_config.get('endpoint', ''),
                    json=request_data,
                    headers=self.api_config.get('headers', {}),
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return self._extract_response(response_data)
                    else:
                        print(f"API request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error sending prompt to API: {e}")
            return None
    
    def _build_request(self, prompt: str) -> Dict[str, Any]:
        """Build request from template with dynamic value substitution."""
        # Generate dynamic values
        self._counter += 1
        values = {
            'prompt': prompt,
            'uuid': str(uuid.uuid4()),
            'timestamp': int(time.time()),
            'random_string': ''.join(random.choices(
                string.ascii_letters + string.digits, k=8
            )),
            'counter': self._counter
        }
        
        # Deep copy template and substitute values
        request_data = deepcopy(self.request_template)
        return self._substitute_values(request_data, values)
    
    def _substitute_values(self, obj: Any, values: Dict[str, Any]) -> Any:
        """Recursively substitute template values in nested structures."""
        if isinstance(obj, str):
            # Simple template substitution
            for key, value in values.items():
                obj = obj.replace(f"{{{{{key}}}}}", str(value))
            return obj
        elif isinstance(obj, dict):
            return {k: self._substitute_values(v, values) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_values(item, values) for item in obj]
        else:
            return obj
    
    def _extract_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract response text using configured path."""
        try:
            path = self.response_extraction['path']
            
            # Navigate nested dictionary using dot notation
            current = response_data
            for key in path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    print(f"Path '{path}' not found in response")
                    return None
            
            return str(current) if current is not None else None
            
        except Exception as e:
            print(f"Error extracting response: {e}")
            return None
