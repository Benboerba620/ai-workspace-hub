# -*- coding: utf-8 -*-
"""Generate a scripted terminal-style demo GIF for ai-workspace-hub README.

Renders frames with Pillow: fake terminal window, typing effect for user
input, line-by-line agent output. Content mirrors the real install flow
in INSTALL-FOR-AI.md (3 questions -> installer -> READY -> first ingest
-> Enhanced Mode API keys). Not a screen recording; the README says so.

Usage: python docs/gen_demo_gif.py [output.gif]   (requires Pillow;
falls back to Microsoft YaHei, so render on Windows or adjust FONT paths)
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 860, 560
PAD_X, PAD_Y = 22, 46
LINE_H = 26
FONT_SIZE = 17
MAX_VISIBLE = (H - PAD_Y - 16) // LINE_H

BG = (24, 24, 37)
TITLEBAR = (35, 35, 52)
FG = (205, 214, 244)
DIM = (127, 132, 156)
GREEN = (166, 227, 161)
CYAN = (137, 220, 235)
YELLOW = (249, 226, 175)
MAUVE = (203, 166, 247)
RED = (243, 139, 168)

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", FONT_SIZE)
    FONT_B = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", FONT_SIZE)
except OSError:
    FONT = ImageFont.truetype("msyh.ttc", FONT_SIZE)
    FONT_B = FONT

TITLE = "my-ai-workspace — AI agent"


def render(lines, cursor=False):
    """lines: list of (text, color, bold). Render one frame."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, W, 34], fill=TITLEBAR)
    for i, c in enumerate([(243, 139, 168), (249, 226, 175), (166, 227, 161)]):
        d.ellipse([14 + i * 22, 11, 26 + i * 22, 23], fill=c)
    tw = d.textlength(TITLE, font=FONT)
    d.text(((W - tw) / 2, 8), TITLE, font=FONT, fill=DIM)
    # body: show tail if overflow
    visible = lines[-MAX_VISIBLE:]
    y = PAD_Y
    for text, color, bold in visible:
        d.text((PAD_X, y), text, font=FONT_B if bold else FONT, fill=color)
        y += LINE_H
    if cursor and visible:
        last = visible[-1]
        lw = d.textlength(last[0], font=FONT_B if last[2] else FONT)
        d.rectangle([PAD_X + lw + 3, y - LINE_H + 3, PAD_X + lw + 13, y - 4],
                    fill=FG)
    return img


frames = []
durations = []
lines = []


def snap(ms, cursor=False):
    frames.append(render(lines, cursor))
    durations.append(ms)


def type_line(prefix, text, color=FG, bold=False, chunk=3, speed=55):
    """Typing effect: prefix appears at once, text appears chunk chars a time."""
    lines.append((prefix, GREEN, True))
    snap(350, cursor=True)
    for i in range(chunk, len(text) + chunk, chunk):
        lines[-1] = (prefix + text[:i], color, bold)
        snap(speed, cursor=True)
    lines[-1] = (prefix + text, color, bold)
    snap(400)


def put(text="", color=FG, bold=False, ms=None):
    lines.append((text, color, bold))
    if ms:
        snap(ms)


def pause(ms):
    snap(ms)


# ---- Scene 1: paste the share sentence -------------------------------
put("", ms=600)
type_line("你 > ", "帮我按这个协议安装 AI Workspace Hub：", speed=45)
put("     https://raw.githubusercontent.com/Benboerba620/", DIM)
put("     ai-workspace-hub/main/INSTALL-FOR-AI.md", DIM, ms=1400)
put()
put("● 读到安装协议全文（Step 0-8）。安装前只问 3 个问题：", CYAN, ms=1100)

# ---- Scene 2: three questions ----------------------------------------
put()
put("● 1/3 工作区放在哪里？（默认：当前目录）", CYAN, ms=700)
type_line("你 > ", "D:/my-ai-workspace")
put("● 2/3 主要用途？（研究 / 写作 / 投研 / 知识库…）", CYAN, ms=700)
type_line("你 > ", "投研 + 个人知识库")
put("● 3/3 已经有 wiki 吗？", CYAN, ms=700)
type_line("你 > ", "没有")
put()

# ---- Scene 3: installer runs -----------------------------------------
put("● 开始安装（标准库安装器，不装任何依赖）…", CYAN, ms=900)
put("  √ AGENTS.md / CLAUDE.md —— agent 入口路由", GREEN, ms=380)
put("  √ wiki/ —— 个人知识库", GREEN, ms=380)
put("  √ inbox/ → output/ —— 输入 → 产出", GREEN, ms=380)
put("  √ hypothesis/ + monitoring/ —— 假设追踪 + 股票池", GREEN, ms=380)
put("  √ tools/podcast + daily-watch —— 播客摄入 + 日报", GREEN, ms=380)
put("  √ workspace/meta/active-context —— 断点续传", GREEN, ms=700)
put()
put("$ python check_workspace.py", YELLOW, ms=800)
put("  Core Mode result: READY", GREEN, True, ms=500)
put("  （不需要 API key，现在就能用）", DIM, ms=2000)

# ---- Scene 4: first ingest -------------------------------------------
put()
type_line("你 > ", "把 inbox/first-note.md 整理进 personal wiki。", speed=40)
put("● 按 wiki/_schema.md 整理…", CYAN, ms=900)
put("  √ wiki/sources/2026-07-02-first-note.md", GREEN, ms=450)
put("  √ wiki/concepts/AI工作流.md", GREEN, ms=450)
put("  √ active-context.md 已记录进度", GREEN, ms=1600)

# ---- Scene 5: Enhanced Mode (API keys) --------------------------------
put()
type_line("你 > ", "再帮我开通行情日报和播客摘要。", speed=40)
put("● 这两项属于 Enhanced Mode，需要填 2 个 key（都有免费档）：", CYAN, ms=900)
put("  · config/daily-watchlist.env —— TUSHARE_TOKEN（A 股行情）", FG, ms=500)
put("  · config/pod2wiki.env —— LLM_API_KEY（播客摘要）", FG, ms=500)
put("  （key 直接粘贴给我；config/ 不进 git，不会被提交）", DIM, ms=1500)
type_line("你 > ", "TUSHARE_TOKEN=3f8a****c2e1", speed=45)
put("  √ 已写入 config/daily-watchlist.env", GREEN, ms=800)
put()
put("$ python check_setup.py", YELLOW, ms=800)
put("  Enhanced Mode: daily-watch READY", GREEN, True, ms=2000)

# ---- Scene 6: closing ------------------------------------------------
put()
put("● 完成。明天开场说「继续」，我会从断点接上。", MAUVE, True, ms=3500)

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "demo.gif")
frames[0].save(out, save_all=True, append_images=frames[1:],
               duration=durations, loop=0, optimize=True)
total = sum(durations) / 1000
print(f"wrote {out}: {len(frames)} frames, {total:.1f}s loop")
