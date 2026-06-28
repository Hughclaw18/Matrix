import os
import re
import requests
from google import genai
from google.genai import types
from langchain_core.prompts import PromptTemplate
from config.constants import PERSONA_PROMPT_TEMPLATE
from utils.tools import TOOLS

# Regex to capture tool call format: TOOL: tool_name(arguments)
TOOL_REGEX = re.compile(r"TOOL:\s*(\w+)\((.+)\)", re.IGNORECASE)

TOOL_INSTRUCTION = """
--- OPERATOR SYSTEM DECODER ENHANCEMENT: TOOLS AVAILABLE ---
You are equipped with the following tools to execute if the query requires external info, math computation, or internal database records:
1. TOOL: web_search(<query_string>) - Performs a live DuckDuckGo web search. Returns top titles, links, and snippets.
2. TOOL: calculate(<mathematical_expression>) - Securely computes numerical operations (e.g. 52 * 102).
3. TOOL: matrix_lore_lookup(<term_string>) - Fetches pre-compiled database files on Matrix characters, ships, or lore.

Usage Rules:
* If the user's query requires external information (such as recent events, releases, movie facts, or calculations) that you do not know, write ONLY:
  TOOL: <tool_name>(<argument>)
  Do not append conversational text or greetings. The operator system will run it and return the data.
* If you already have the tool execution result or do not need a tool to answer, proceed to formulate your final conversational response in the Oracle's characteristic tone.
"""

class LLMService:
    def __init__(self):
        # Configure Gemini Client
        gemini_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_client = None
        if gemini_key:
            self.gemini_client = genai.Client(api_key=gemini_key)
            
        self.prompt_template = PromptTemplate.from_template(PERSONA_PROMPT_TEMPLATE)

    def get_chat_response(self, provider: str, model_name: str, context: str, question: str) -> str:
        formatted_prompt = self.prompt_template.format(context=context, question=question)
        
        # Append tool availability instructions to system prompt
        full_prompt = formatted_prompt + "\n" + TOOL_INSTRUCTION
        provider = provider.lower()

        # ReAct execution loop (max 2 iterations to avoid loops)
        for _ in range(2):
            response = self._execute_model_call(provider, model_name, full_prompt)
            
            # Check if output contains a tool invocation
            match = TOOL_REGEX.search(response)
            if not match:
                # If no tool requested, this is the final conversational output!
                return response
            
            tool_name = match.group(1).lower().strip()
            tool_arg = match.group(2).strip()
            
            # Strip outer quotes if any
            if (tool_arg.startswith('"') and tool_arg.endswith('"')) or \
               (tool_arg.startswith("'") and tool_arg.endswith("'")):
                tool_arg = tool_arg[1:-1]
            
            # Execute tool
            if tool_name in TOOLS:
                print(f"[Agent Tool Execution] Running {tool_name} with: '{tool_arg}'")
                tool_output = TOOLS[tool_name](tool_arg)
            else:
                tool_output = f"Error: Tool '{tool_name}' is not recognized."

            # Feed tool execution result back into context history
            full_prompt += f"\n\nTOOL CALL EXECUTED: TOOL: {tool_name}({tool_arg})\nSYSTEM DATA RETRIEVED:\n{tool_output}\n\nProceed to formulate your final response with this data or call another tool if needed."

        # Final fallback call if max iterations exceeded
        return self._execute_model_call(provider, model_name, full_prompt)

    def _execute_model_call(self, provider: str, model_name: str, prompt: str) -> str:
        if provider == "gemini":
            return self._get_gemini_response(model_name, prompt)
        elif provider == "nvidia":
            return self._get_nvidia_response(model_name, prompt)
        elif provider == "groq":
            return self._get_groq_response(model_name, prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    def _get_gemini_response(self, model_name: str, prompt: str) -> str:
        if not self.gemini_client:
            return "Gemini API Error: GOOGLE_API_KEY environment variable is not set."
        try:
            model_clean = model_name
            if model_name.startswith("models/"):
                model_clean = model_name.replace("models/", "")
                
            completion = self.gemini_client.models.generate_content(
                model=model_clean,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    temperature=0.6,
                    top_p=0.7
                )
            )
            return completion.text
        except Exception as e:
            return f"Gemini API Error: {str(e)}"

    def _get_nvidia_response(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return "NVIDIA API Error: NVIDIA_API_KEY environment variable is not set."
            
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "top_p": 0.7,
            "max_tokens": 1024
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code != 200:
                try:
                    error_json = response.json()
                    if "error" in error_json and "message" in error_json["error"]:
                        return f"NVIDIA API Error: {error_json['error']['message']}"
                    return f"NVIDIA API Error ({response.status_code}): {error_json}"
                except Exception:
                    return f"NVIDIA API Error ({response.status_code}): {response.text[:200]}"
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"NVIDIA Connection Error: {str(e)}"

    def _get_groq_response(self, model_name: str, prompt: str) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Groq API Error: GROQ_API_KEY environment variable is not set."
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 1024
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code != 200:
                try:
                    error_json = response.json()
                    if "error" in error_json and "message" in error_json["error"]:
                        return f"Groq API Error: {error_json['error']['message']}"
                    return f"Groq API Error ({response.status_code}): {error_json}"
                except Exception:
                    return f"Groq API Error ({response.status_code}): {response.text[:200]}"
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Groq Connection Error: {str(e)}"
