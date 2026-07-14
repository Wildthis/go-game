# 围棋人机对战 (Go Game)

Python 围棋引擎 + Vue 3 前端，支持人机对战。

## 功能

- 支持 9×9、13×13、19×19 三种棋盘
- 完整的围棋规则：提子、打劫（Ko）、自杀禁手、连续pass结束
- AI 对手 3 级难度：吃子优先、救急、局部战斗
- **命令行界面** 和 **Web UI** 两种玩法
- 实时计分、棋谱记录

## 快速开始

### 方式一：Web 界面（推荐）

```bash
# 启动后端服务（端口 8765）
python3 server.py

# 浏览器打开 http://localhost:8765
```

### 方式二：命令行

```bash
python3 main.py           # 19路，难度2
python3 main.py 9 1       # 9路，难度1
python3 main.py 13 3      # 13路，难度3
```

## 项目结构

```
go-game/
├── index.html          # Vue 3 前端（单文件 SPA）
├── server.py           # FastAPI 后端服务
├── board.py            # 棋盘逻辑，围棋规则
├── ai.py               # AI 对手，策略引擎
├── main.py             # 命令行交互界面
├── test_game.py        # 自动化测试（12项）
├── README.md
└── requirements.txt
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/game/new` | 开始新游戏 `{"size":19,"difficulty":2}` |
| POST | `/api/game/play` | 人类落子 `{"row":4,"col":4}` |
| POST | `/api/game/pass` | 人类 pass |
| POST | `/api/game/resign` | 人类认输 |
| GET | `/api/game/state` | 获取当前状态 |
| GET | `/api/game/legal` | 获取合法落子点 |

## 依赖

- Python 3.12+ + `fastapi` + `uvicorn`
- 浏览器（Vue 3 通过 CDN 加载，无需构建）
