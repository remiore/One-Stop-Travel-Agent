try:
    from agno.tools.mcp import MultiMCPTools
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")

try:
    from agno.models.google import Gemini
    print("Gemini import successful")
except ImportError as e:
    print(f"Gemini import failed: {e}")
