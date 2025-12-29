from typing import List, Dict, Any, Optional
import json

class PromptEngineer:
    """
    Constructs LLM prompts using DeepMind-style principles:
    1. Context Anchor (Role + Goal)
    2. Constraint Stack (Boundaries)
    3. Format Specification (JSON Schema)
    4. Evidence Demand (Assumptions/Trace)
    """

    def __init__(self, role: str, goal: str):
        self.role = role
        self.goal = goal
        self.context_items: List[str] = []
        self.constraints: List[str] = []
        self.format_instruction = ""
        self.evidence_required = False

    def add_context(self, context: str):
        """Add context/background information."""
        self.context_items.append(context)
        return self

    def add_section(self, title: str):
        """Add a labeled section header to the prompt."""
        self.context_items.append(f"\n--- {title.upper()} ---")
        return self

    def add_constraint(self, constraint: str):
        """Add a strict boundary/constraint."""
        self.constraints.append(constraint)
        return self

    def require_evidence(self):
        """Force the model to list assumptions/reasoning first."""
        self.evidence_required = True
        return self

    def set_output_format(self, schema_desc: str):
        """Define the JSON structure for the output."""
        self.format_instruction = f"""
        OUTPUT FORMAT:
        You must output a VALID JSON object adhering to this schema:
        {schema_desc}
        Do not include markdown formatting (```json) around the output. Just the raw JSON string.
        """
        return self

    def build_system_prompt(self) -> str:
        """Construct the final system prompt."""
        
        # 1. Context Anchor
        prompt = f"ROLE: {self.role}\n"
        prompt += f"GOAL: {self.goal}\n\n"

        # 2. Context Items
        if self.context_items:
            prompt += "CONTEXT:\n"
            for item in self.context_items:
                prompt += f"- {item}\n"
            prompt += "\n"

        # 3. Constraint Stack
        if self.constraints:
            prompt += "CONSTRAINTS (MUST FOLLOW):\n"
            for constraint in self.constraints:
                prompt += f"- {constraint}\n"
            prompt += "\n"

        # 4. Evidence Output Instruction (Implicit in JSON schema often, but reinforced here)
        if self.evidence_required:
            prompt += "REQUIREMENT: You must analyze the evidence and list your assumptions before generating the final content.\n\n"

        # 5. Format Specification
        if self.format_instruction:
            prompt += f"{self.format_instruction}\n"

        return prompt

    @staticmethod
    def parse_json_output(response_text: str) -> Dict[str, Any]:
        """Safely parse the LLM output, handling potential markdown wrapping."""
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        
        try:
            return json.loads(clean_text.strip())
        except json.JSONDecodeError as e:
            # Fallback: simple text return wrapped in dict if parsing fails
            return {"error": "json_parse_error", "raw_content": response_text}
