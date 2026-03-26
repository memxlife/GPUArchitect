from llm.openai_client import call_llm

def generate_memory_kernel_variant(n: int, threads: int) -> str:
    system = "You are a CUDA expert. Generate a CUDA kernel snippet only."
    user = f"""
Modify a memory copy CUDA kernel with:
- n = {n}
- threads per block = {threads}

Only output kernel code, no explanation.
"""

    return call_llm(system, user)
