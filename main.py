from fastapi import FastAPI
from pydantic import BaseModel
import subprocess

app = FastAPI()

# Pre-download the 5M parameter Maia model on startup so the first request isn't slow
subprocess.run(["maia3-cache", "--model", "maia3-5m"], capture_output=True)

class ChessRequest(BaseModel):
    fen: str
    movetime: int = 500  # Default 500ms think time

@app.post("/get_move")
async def get_move(request: ChessRequest):
    try:
        # Start the real Maia-3 UCI engine process
        process = subprocess.Popen(
            ["maia3-5m"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send standard UCI commands to the engine
        process.stdin.write("uci\n")
        process.stdin.write(f"position fen {request.fen}\n")
        process.stdin.write(f"go movetime {request.movetime}\n")
        process.stdin.flush()
        
        # Read the output to find the "bestmove"
        best_move = None
        for line in process.stdout:
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break
                
        process.terminate()
        
        if best_move:
            return {"move": best_move, "engine": "Real Maia-3 (5M)"}
        else:
            return {"error": "Engine did not return a move"}
            
    except Exception as e:
        return {"error": str(e)}