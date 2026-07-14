#!/usr/bin/env python3
"""
围棋人机对战 - FastAPI 后端服务
提供 REST API 供 Vue 前端调用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from board import Board
from ai import GoAI

app = FastAPI(title="Go Game API", version="1.0.0")

# 挂载静态文件（index.html）
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# CORS - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic models ----------

class NewGameRequest(BaseModel):
    size: int = 19
    difficulty: int = 2


class MoveRequest(BaseModel):
    row: int
    col: int


class GameStateResponse(BaseModel):
    grid: list[list[int]]
    size: int
    turn: int  # 1=黑, 2=白
    last_move: Optional[list[int]]
    black_count: int
    white_count: int
    empty_count: int
    game_over: bool
    winner: Optional[str]
    message: str


# ---------- 全局状态 ----------
board_instance: Optional[Board] = None
ai_instance: Optional[GoAI] = None
turn_counter = 0


def get_state() -> dict:
    global board_instance, ai_instance, turn_counter
    if board_instance is None:
        return {}
    black, white, empty = board_instance.count_stones()
    winner = None
    if board_instance.is_game_over_by_pass():
        if black > white + 7.5:
            winner = "black"
        else:
            winner = "white"
    return {
        "grid": board_instance.grid,
        "size": board_instance.size,
        "turn": turn_counter,
        "last_move": list(board_instance.last_move) if board_instance.last_move else None,
        "black_count": black,
        "white_count": white,
        "empty_count": empty,
        "game_over": winner is not None,
        "winner": winner,
    }


# ---------- API ----------

@app.post("/api/game/new")
async def new_game(req: NewGameRequest):
    global board_instance, ai_instance, turn_counter
    if req.size not in (9, 13, 19):
        raise HTTPException(400, "棋盘大小仅支持 9, 13, 19")
    if req.difficulty not in (1, 2, 3):
        raise HTTPException(400, "难度仅支持 1, 2, 3")
    board_instance = Board(req.size)
    ai_instance = GoAI(board_instance, Board.WHITE, req.difficulty)
    turn_counter = 0
    state = get_state()
    state["message"] = "新游戏开始，黑方先行"
    state["difficulty"] = req.difficulty
    return state


@app.post("/api/game/pass")
async def pass_turn():
    global board_instance, turn_counter
    if board_instance is None:
        raise HTTPException(400, "请先开始新游戏")
    # 黑方(pass)
    board_instance.pass_turn(Board.BLACK)
    turn_counter += 1
    if board_instance.is_game_over_by_pass():
        black, white, _ = board_instance.count_stones()
        winner = "黑方胜" if black > white + 7.5 else "白方胜"
        return get_state() | {"message": f"双方连续pass，{winner}"}
    return get_state() | {"message": "黑方pass"}


@app.post("/api/game/resign")
async def resign():
    global board_instance
    if board_instance is None:
        raise HTTPException(400, "请先开始新游戏")
    return get_state() | {"message": "黑方认输，白方胜！", "winner": "white"}


@app.post("/api/game/play")
async def human_play(req: MoveRequest):
    global board_instance, ai_instance, turn_counter
    if board_instance is None:
        raise HTTPException(400, "请先开始新游戏")

    # 人类落子（黑方）
    error = board_instance.play(req.row, req.col, Board.BLACK)
    if error:
        msg = {"ko": "打劫！此处不能落子", "suicide": "自杀禁手！", "occupied": "此处已有棋子", "out_of_bounds": "超出棋盘范围"}
        raise HTTPException(400, msg.get(error, f"非法落子: {error}"))

    turn_counter += 1
    board_instance.last_move = (req.row, req.col)

    # 检查游戏结束
    if board_instance.is_game_over_by_pass():
        black, white, _ = board_instance.count_stones()
        winner = "黑方胜" if black > white + 7.5 else "白方胜"
        return get_state() | {"message": f"游戏结束，{winner}"}

    # AI 落子（白方）
    ai_move = ai_instance.best_move()
    if ai_move:
        board_instance.play(ai_move[0], ai_move[1], Board.WHITE)
        board_instance.last_move = ai_move
        turn_counter += 1

    # 再次检查结束
    if board_instance.is_game_over_by_pass():
        black, white, _ = board_instance.count_stones()
        winner = "黑方胜" if black > white + 7.5 else "白方胜"
        return get_state() | {"message": f"游戏结束，{winner}"}

    return get_state() | {"message": "你的回合 - 请落子"}


@app.get("/api/game/state")
async def get_game_state():
    if board_instance is None:
        raise HTTPException(400, "请先开始新游戏")
    return get_state() | {"message": ""}


@app.get("/api/game/legal")
async def get_legal_moves():
    global board_instance
    if board_instance is None:
        raise HTTPException(400, "请先开始新游戏")
    moves = board_instance.get_legal_moves(Board.BLACK)
    return {"moves": [list(m) for m in moves]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
