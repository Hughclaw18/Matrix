import urllib.parse
import requests
import math
from bs4 import BeautifulSoup

def web_search(query: str) -> str:
    """Executes a web search on DuckDuckGo and returns title, link, and snippets of top 5 results."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Search failed with status code {response.status_code}."
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.find_all("div", class_="result__body")[:5]:
            title_elem = item.find("a", class_="result__url")
            snippet_elem = item.find("a", class_="result__snippet")
            if title_elem and snippet_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem["href"]
                snippet = snippet_elem.get_text(strip=True)
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
                
        if not results:
            return "No relevant search results found."
            
        return "\n".join(results)
    except Exception as e:
        return f"Error executing web search: {str(e)}"

def calculate(expression: str) -> str:
    """Evaluates mathematical expressions securely."""
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        # Strict sanitation to prevent arbitrary code execution
        cleaned = "".join(c for c in expression if c in "0123456789+-*/()., ")
        result = eval(cleaned, {"__builtins__": None}, allowed_names)
        return f"Math Result: {result}"
    except Exception as e:
        return f"Math execution error: {str(e)}"

MATRIX_FACTS = {
    "architect": "The Architect is the creator of the Matrix. He is a highly logical program who designed the system to control human minds and balance equations.",
    "zion": "Zion is the last human city on Earth, located deep underground near the Earth's core for warmth. It serves as the staging ground for the human resistance.",
    "nebuchadnezzar": "The Nebuchadnezzar is the hovercraft commanded by Morpheus. It was destroyed by Sentinels in the first movie using an EMP.",
    "agent smith": "Agent Smith is a rogue program who originally worked as an Agent of the Matrix. After Neo destroyed him, he became a virus capable of copying himself onto other programs and humans.",
    "trinity": "Trinity is a first officer of the Nebuchadnezzar and Neo's love interest. She dies in the real world during the final assault on the Machine City in Matrix Revolutions.",
    "morpheus": "Morpheus is the captain of the Nebuchadnezzar who searched for the One (Neo). He is a believer in the prophecy of the Oracle.",
}

def matrix_lore_lookup(term: str) -> str:
    """Looks up pre-compiled Matrix trilogy facts and details."""
    term = term.lower().strip()
    for key, value in MATRIX_FACTS.items():
        if key in term or term in key:
            return f"Oracle Database Record for '{key}': {value}"
    return "Term not found in core Oracle database records. Recommend performing a web search."

# Map tool names to actual functions
TOOLS = {
    "web_search": web_search,
    "calculate": calculate,
    "matrix_lore_lookup": matrix_lore_lookup
}
