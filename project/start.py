"""WanderGraph 一键启动（健壮版）

与旧版的差异（见 ISSUES #19）：
- 后端/前端子进程的 stdout/stderr 汇流到本主终端（带 [backend]/[frontend] 前缀），
  不再各自开新控制台窗口 —— 后端任何启动期崩溃都会直接打印在眼前，且杜绝
  "随手关掉后端那个窗口导致 8000 静默死亡、前端代理打死端口表现为超时" 的失败模式。
- 后端不再 --reload（demo 一键启动无需热重载，--reload 在 Windows 上的 reloader
  子进程对独立控制台环境较脆弱）。
- 健康检查改为真实 GET /api/health（端口能 connect 不代表 app ready）。
- 退出时按进程树终止子进程（Windows taskkill /T），不留孤儿。
"""
import subprocess
import threading
import time
import sys
import os
import socket
import webbrowser
import urllib.request
import json

# Windows 控制台默认 GBK 编码，子进程的 UTF-8 日志（含中文/替换符）写回 stdout 会
# 抛 UnicodeEncodeError 把日志汇流线程崩掉（见 ISSUES #19）。重配为 utf-8 + replace。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def check_port(port: int) -> bool:
    """TCP 端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("localhost", port)) == 0


def health_ok(port: int, timeout: float = 2.0) -> bool:
    """真实探活 GET /api/health（端口开 ≠ app ready）"""
    try:
        r = urllib.request.urlopen(
            f"http://localhost:{port}/api/health", timeout=timeout)
        return r.status == 200
    except Exception:
        return False


def wait_for_health(port: int, timeout: int = 40, name: str = "") -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if health_ok(port):
            print(f"  [{name}] 已就绪 (health ok on {port})")
            return True
        time.sleep(0.5)
    print(f"  [{name}] 超时 ({timeout}s，详见上方该进程的日志输出)")
    return False


def wait_for_port(port: int, timeout: int = 30, name: str = "") -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if check_port(port):
            print(f"  [{name}] 已就绪 (port {port})")
            return True
        time.sleep(0.5)
    print(f"  [{name}] 超时 ({timeout}s)")
    return False


def stream(prefix: str, pipe):
    """把子进程 stdout/stderr 带前缀打印到主终端"""
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            sys.stdout.write(f"[{prefix}] {line}")
            sys.stdout.flush()
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def spawn(label: str, cmd, cwd, env=None, shell=False):
    """启动子进程并汇流输出到主终端（不开新窗口）"""
    # 子进程（尤其是后端 python）默认用 Windows GBK 编码 stdout，导致其中文 print()
    # 被父进程按 utf-8 解码出乱码。强制子进程用 utf-8 输出。
    if env is None:
        env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
        encoding="utf-8",
        errors="replace",
    )
    t = threading.Thread(target=stream, args=(label, proc.stdout), daemon=True)
    t.start()
    proc._stream_thread = t
    return proc


def check_ollama() -> bool:
    try:
        resp = urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=3)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        if "qwen3:8b" in models:
            print(f"  Ollama: OK (模型: qwen3:8b)")
            return True
        if models:
            print(f"  Ollama: OK，但没有 qwen3:8b (可用: {', '.join(models)})")
            print("  请运行: ollama pull qwen3:8b")
            return False
        print("  Ollama: 运行中，但没有模型")
        print("  请运行: ollama pull qwen3:8b")
        return False
    except Exception:
        return False


def kill_tree(proc):
    """按进程树终止子进程（Windows）"""
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True)
        else:
            import signal
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main():
    print("=" * 50)
    print("  WanderGraph 一键启动")
    print("=" * 50)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_dir, "backend")
    frontend_dir = os.path.join(project_dir, "frontend")

    procs = []

    try:
        # ━━━ Step 1: 检查 Ollama ━━━
        print("\n[1/4] 检查 Ollama...")
        if not check_ollama():
            print("  Ollama 未运行，请先启动: ollama serve")
            print("  然后重新运行此脚本")
            sys.exit(1)

        # ━━━ Step 2: 检查端口 ━━━
        print("\n[2/4] 检查端口...")
        skip_backend = check_port(8000)
        if skip_backend:
            print("  端口 8000 已被占用，假设后端已在运行，跳过后端启动")
        skip_frontend = check_port(5173)
        if skip_frontend:
            print("  端口 5173 已被占用，假设前端已在运行，跳过前端启动")

        # ━━━ Step 3: 启动后端 ━━━
        if not skip_backend:
            print("\n[3/4] 启动后端 (uvicorn, 日志汇流到本终端)...")
            backend_proc = spawn(
                "backend",
                [sys.executable, "-m", "uvicorn", "app.main:app",
                 "--port", "8000", "--host", "127.0.0.1"],
                cwd=backend_dir,
            )
            procs.append(backend_proc)
            if not wait_for_health(8000, timeout=40, name="Backend"):
                print("  后端启动失败 —— 请向上查看 [backend] 行找到真实报错")
                sys.exit(1)
        else:
            print("\n[3/4] 跳过后端（已在运行）")

        # ━━━ Step 4: 启动前端 ━━━
        frontend_port = 5173
        if not skip_frontend:
            print("\n[4/4] 启动前端 (pnpm dev, 日志汇流到本终端)...")
            env = os.environ.copy()
            env["CI"] = "true"  # 避免 pnpm 在非交互终端卡住（见 ISSUES #18）
            frontend_proc = spawn(
                "frontend",
                "pnpm dev",  # shell=True：Windows 上 pnpm 是 pnpm.cmd 批处理 shim
                cwd=frontend_dir,
                env=env,
                shell=True,
            )
            procs.append(frontend_proc)
            # Vite 可能分配 5173-5177
            frontend_port = 5173
            ok = False
            while frontend_port <= 5177:
                if wait_for_port(frontend_port, timeout=30000, name="Frontend"):
                    ok = True
                    break
                frontend_port += 1
            if not ok:
                print("  前端启动失败 —— 请向上查看 [frontend] 行找到真实报错")
                sys.exit(1)
        else:
            print("\n[4/4] 跳过前端（已在运行）")

        # ━━━ 打开浏览器 ━━━
        print("\n" + "=" * 50)
        print("  全部启动完成!")
        print("=" * 50)
        print(f"  前端:  http://localhost:{frontend_port}")
        print(f"  后端:  http://localhost:8000/docs")
        print("  按 Ctrl+C 退出（会同时关闭后端和前端）")
        print()

        time.sleep(1)
        webbrowser.open(f"http://localhost:{frontend_port}")

        # 保持运行；若任一子进程意外退出则提示
        while True:
            for p in procs:
                rc = p.poll()
                if rc is not None:
                    print(f"  [警告] 子进程已退出 (rc={rc})，请向上查看日志")
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n已退出，正在关闭后端和前端...")
    finally:
        for p in procs:
            kill_tree(p)
        print("已清理子进程。")


if __name__ == "__main__":
    main()
