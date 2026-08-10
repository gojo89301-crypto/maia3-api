from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess

app = FastAPI()

# 🚨 CRITICAL FIX: Allow Chess.com to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Maia-3 API is running successfully! Send POST requests to /get_move"}

# Pre-download the 5M parameter Maia model on startup
subprocess.run(["maia3-cache", "--model", "maia3-5m"], capture_output=True)

class ChessRequest(BaseModel):
    fen: str
    movetime: int = 500

@app.post("/get_move")
async def get_move(request: ChessRequest):
    try:
        process = subprocess.Popen(
            ["maia3-5m"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        process.stdin.write("uci\n")
        process.stdin.write(f"position fen {request.fen}\n")
        process.stdin.write(f"go movetime {request.movetime}\n")
        process.stdin.flush()
        
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
