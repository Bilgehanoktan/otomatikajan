import os
import re

MAPPINGS = {
    r'\bfrom db\b': 'from packages.persistence',
    r'\bimport db\b': 'import packages.persistence as db',
    r'\bdb\.': 'packages.persistence.',
    
    r'\bfrom observability\b': 'from packages.observability',
    r'\bobservability\.': 'packages.packages.observability.',
    
    r'\bfrom llm\b': 'from packages.llm_gateway',
    r'\bllm\.': 'packages.llm_gateway.',
    
    r'\bfrom quality\b': 'from packages.quality_assurance',
    r'\bquality\.': 'packages.quality_assurance.',
    
    r'\bfrom memory\b': 'from packages.memory',
    r'\bmemory\.': 'packages.packages.memory.',
    
    r'\bfrom repair\b': 'from packages.repair_engine',
    r'\brepair\.': 'packages.repair_engine.',
    
    r'\bfrom healing\b': 'from packages.healing',
    r'\bhealing\.': 'packages.packages.healing.',
    
    r'\bfrom improve\b': 'from packages.improvement_engine',
    r'\bimprove\.': 'packages.improvement_engine.',
    
    r'\bfrom agents\b': 'from packages.orchestration.agi',
    r'\bagents\.': 'packages.orchestration.agi.',
    
    r'\bfrom skills\b': 'from packages.skills',
    r'\bskills\.': 'packages.packages.skills.',
    
    r'\bfrom auth\b': 'from apps.api.routers.auth',
    r'\bauth\.': 'apps.api.routers.apps.api.routers.auth.',

    r'\bcore\.agi\b': 'packages.orchestration.agi',
    r'\bcore\.job_queue\b': 'packages.orchestration.application.job_queue',
}

EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', 'packages', 'node_modules', '.gemini'}

def sterilize():
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if not file.endswith('.py'):
                continue
            
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for pattern, replacement in MAPPINGS.items():
                new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Sterilized: {path}")

if __name__ == "__main__":
    sterilize()
