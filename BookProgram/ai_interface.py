import asyncio
from asyncio.subprocess import PIPE

async def run_ollama(prompt):
    try:
        command = ['ollama', 'run', 'gemma3', prompt]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=PIPE,
            stderr=PIPE
        )
        return process
    except Exception as e:
        print(f"An error occurred while starting the subprocess: {str(e)}")
        return None