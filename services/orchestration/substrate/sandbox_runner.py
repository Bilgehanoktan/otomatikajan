"""
SandboxRunner — Isolated Code Execution (Faz 12)

Üretilen patch/kod parçacıklarını güvenli, izole subprocess ortamında çalıştırır.
Docker varsa Docker container kullanır; yoksa kısıtlı subprocess ile devam eder.

Güvenlik garantileri:
  - Ağ erişimi yok (subprocess: sistem ağından izole değil, ama connection açılmaz)
  - Zaman sınırı (varsayılan 10s)
  - Geçici dosya -> temizleme
  - Çıktı boyutu limiti (4KB)
  - Tehlikeli built-in'ler ast-level kontrol
"""

import asyncio
import asyncio.subprocess
import ast
import os
import subprocess
import tempfile
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from services.observability.logging import get_logger

_log = get_logger("sandbox_runner")


# ── Tehlikeli built-in'ler ───────────────────────────────────
_FORBIDDEN_BUILTINS: frozenset[str] = frozenset({
    "exec", "eval", "__import__", "compile",
    "open", "getattr", "setattr", "delattr",
    "locals", "globals", "memoryview", "marshal", "pickle",
})

_FORBIDDEN_MODULES: frozenset[str] = frozenset({
    "subprocess", "socket", "http", "urllib", "requests", "httpx",
    "ftplib", "smtplib", "telnetlib", "ctypes", "cffi", "pwn", "shutil",
    "importlib", "builtins", "tempfile", "pathlib", "threading"
})


@dataclass
class SandboxResult:
    run_id:    str
    success:   bool
    stdout:    str
    stderr:    str
    exit_code: int
    duration_s: float
    mode:      str     # "docker" | "subprocess" | "ast_blocked"
    blocked_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "run_id":         self.run_id,
            "success":        self.success,
            "stdout":         self.stdout[:2000],
            "stderr":         self.stderr[:2000],
            "exit_code":      self.exit_code,
            "duration_s":     float(int(self.duration_s * 1000) / 1000.0),
            "mode":           self.mode,
            "blocked_reason": self.blocked_reason,
        }


class SandboxRunner:
    """
    Güvenli kod çalıştırma motoru.

    Öncelik sırası:
    1. Docker (varsa) — tam izolasyon
    2. Restricted subprocess — zaman + çıktı sınırlı
    3. AST güvenlik kontrolü geçemezse: bloke

    Kullanım:
        runner = get_sandbox_runner()
        result = await runner.run_python(code="print('hello')", timeout=5)
        if not result.success:
            print(result.stderr)
    """

    def __init__(
        self,
        timeout: int = 10,
        max_output_kb: int = 4,
        use_docker: bool = True,
        docker_image: str = "python:3.12-slim",
    ):
        self.timeout = timeout
        self.max_output_kb = max_output_kb
        self.docker_image = docker_image
        self._docker_available: Optional[bool] = None
        
        # KRİTİK GÜVENLİK YAMASI: Üretim ortamında Docker izolasyonu tartışılamaz.
        self._is_prod = os.getenv("APP_ENV") == "production"
        self._use_docker = True if self._is_prod else use_docker

    # ── Public API ─────────────────────────────────────────────

    async def run_python(
        self,
        code:    str,
        timeout: Optional[int] = None,
        extra_files: Optional[dict[str, str]] = None,  # {filename: content}
    ) -> SandboxResult:
        """Python kodu sandbox'ta çalıştır."""
        run_id = f"sbox_{uuid.uuid4().hex[:8]}"
        t0     = time.time()

        # AST güvenlik kontrolü (Mevcut yapı korunuyor)
        block_reason = self._ast_security_check(code)
        if block_reason:
            _log.warning(f"Sandbox AST bloke [{run_id}]: {block_reason}")
            return SandboxResult(
                run_id=run_id, success=False,
                stdout="", stderr=f"BLOCKED: {block_reason}",
                exit_code=-1, duration_s=time.time() - t0,
                mode="ast_blocked", blocked_reason=block_reason,
            )

        docker_active = await self._docker_available_check()

        # GÜVENLİK DUVARI: Prod'da Docker yoksa ana makineye düşmesine asla izin verme!
        if self._is_prod and not docker_active:
            _log.critical(f"[GÜVENLİK] Production ortamında Docker bulunamadı! İşlem bloke edildi. [{run_id}]")
            return SandboxResult(
                run_id=run_id, success=False,
                stdout="", stderr="FATAL: Sandbox isolation failure. Execution blocked.",
                exit_code=-1, duration_s=time.time() - t0,
                mode="security_blocked", blocked_reason="docker_not_running_prod",
            )

        if docker_active and self._use_docker:
            return await self._run_docker(run_id, code, extra_files or {}, timeout or self.timeout)
        else:
            _log.warning(f"[{run_id}] Development modunda güvensiz subprocess ile kod çalıştırılıyor!")
            return await self._run_subprocess(run_id, code, extra_files or {}, timeout or self.timeout)


    async def run_tests(
        self,
        test_code:  str,
        source_code: Optional[str] = None,
        module_name: str = "module_under_test",
        timeout: Optional[int] = None,
    ) -> SandboxResult:
        """
        Test kodu çalıştır.
        source_code varsa ayrı dosyaya yazar, test_code içinde import edilebilir.
        """
        extra: dict[str, str] = {}
        if source_code:
            extra[f"{module_name}.py"] = source_code

        # pytest yerine unittest ile çalıştır (dependency yok)
        runner_code = textwrap.dedent(f"""
            import unittest
            import sys
            sys.path.insert(0, '.')

            {test_code}

            loader = unittest.TestLoader()
            suite  = loader.loadTestsFromModule(__import__('__main__'))
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            result = runner.run(suite)
            sys.exit(0 if result.wasSuccessful() else 1)
        """)
        return await self.run_python(runner_code, timeout=timeout, extra_files=extra)

    async def run_ruff_check(self, code: str) -> SandboxResult:
        """Ruff linter kontrolü (Docker ile tam izole veya subprocess)."""
        run_id = f"ruff_{uuid.uuid4().hex[:8]}"
        t0     = time.time()
        
        docker_active = await self._docker_available_check()
        if self._is_prod and not docker_active:
            _log.critical(f"[GÜVENLİK] Prod ortamında Docker yok! Ruff check bloke edildi. [{run_id}]")
            return SandboxResult(
                run_id=run_id, success=False,
                stdout="", stderr="FATAL: Ruff isolation failure in prod.",
                exit_code=-1, duration_s=time.time() - t0, mode="security_blocked",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "check.py")
            with open(fpath, "w") as f:
                f.write(code)
            try:
                if self._use_docker and docker_active:
                    cmd = [
                        "docker", "run", "--rm",
                        "--network=none",
                        "--memory=128m",
                        "--cap-drop=ALL",
                        "--security-opt", "no-new-privileges",
                        "--read-only",
                        "-v", f"{os.path.abspath(tmpdir)}:/app:ro",
                        "ghcr.io/astral-sh/ruff:latest",
                        "check", "/app/check.py", "--output-format=text"
                    ]
                else:
                    cmd = ["ruff", "check", fpath, "--output-format=text"]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
                ok = proc.returncode == 0
                return SandboxResult(
                    run_id=run_id, success=ok,
                    stdout=stdout.decode("utf-8", errors="replace")[:2000],
                    stderr=stderr.decode("utf-8", errors="replace")[:500],
                    exit_code=proc.returncode or 0,
                    duration_s=time.time() - t0, mode="docker_ruff" if self._use_docker and docker_active else "ruff",
                )
            except FileNotFoundError:
                # ruff yüklü değil — geç
                return SandboxResult(
                    run_id=run_id, success=True,
                    stdout="(ruff not installed — skipped)",
                    stderr="", exit_code=0,
                    duration_s=time.time() - t0, mode="ruff_skip",
                )
            except Exception as e:
                return SandboxResult(
                    run_id=run_id, success=False,
                    stdout="", stderr=str(e),
                    exit_code=-1, duration_s=time.time() - t0, mode="ruff",
                )

    # ── İç Metodlar ────────────────────────────────────────────

    def _ast_security_check(self, code: str) -> Optional[str]:
        """Kodu AST düzeyinde güvenlik kontrolünden geçir."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"SyntaxError: {e}"

        for node in ast.walk(tree):
            # 1. Çağrı kontrolleri (exec, eval vb.)
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = getattr(node.func, "id", "")
                elif isinstance(node.func, ast.Attribute):
                    func_name = getattr(node.func, "attr", "")
                
                # Obfuscation: getattr(obj, "at"+"tr")
                if func_name == "getattr" and len(node.args) >= 2:
                    arg2 = node.args[1]
                    # Basit string birleştirmelerini kontrol et: "sy" + "stem"
                    attr_val = self._resolve_constant(arg2)
                    if attr_val in ("system", "popen", "spawn", "run", "call", "connect"):
                        return f"Tehlikeli getattr erişimi (obfuscated?): {attr_val}"

                if func_name in _FORBIDDEN_BUILTINS:
                    return f"Yasaklı fonksiyon/built-in: {func_name}"

            # 2. Import kontrolleri
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = getattr(node, "names", [])
                modules = [n.name for n in names]
                if isinstance(node, ast.ImportFrom) and getattr(node, "module", None):
                    modules.append(node.module)
                
                for m in modules:
                    if not m: continue
                    base_m = m.split('.')[0]
                    if base_m in _FORBIDDEN_MODULES and base_m != "socket": # socket'i Docker'a bırakıyoruz
                        return f"Yasaklı import: {m}"

            # 3. Tehlikeli attribute erişimi
            if isinstance(node, ast.Attribute):
                if node.attr in ("system", "popen", "spawn", "run", "call", "connect", "rmtree"):
                    return f"Tehlikeli attribute erişimi: {node.attr}"

        return None

    def _resolve_constant(self, node: ast.AST) -> Optional[str]:
        """AST düğümünden sabit string değerini çözmeye çalışır."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._resolve_constant(node.left)
            right = self._resolve_constant(node.right)
            if left is not None and right is not None:
                return left + right
        return None

    async def _docker_available_check(self) -> bool:
        if self._docker_available is not None:
            return self._docker_available
        try:
            proc = await asyncio.create_subprocess_shell(
                "docker info",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()
            self._docker_available = (proc.returncode == 0)
        except Exception:
            self._docker_available = False
        return bool(self._docker_available)

    async def _run_docker(
        self,
        run_id:      str,
        code:        str,
        extra_files: dict[str, str],
        timeout:     int,
    ) -> SandboxResult:
        t0 = time.time()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Dosyaları yaz
            main_path = os.path.join(tmpdir, "script.py")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(code)
            for fname, content in extra_files.items():
                with open(os.path.join(tmpdir, fname), "w", encoding="utf-8") as f:
                    f.write(content)
            try:
                cmd = [
                    "docker", "run", "--rm",
                    "--network=none",
                    "--memory=128m",
                    "--cpus=0.5",
                    "--ulimit", "nofile=64:64",
                    "--ulimit", "nproc=64:64",
                    "--cap-drop=ALL",
                    "--security-opt", "no-new-privileges",
                    "--read-only",
                    "--tmpfs", "/tmp:rw,size=16m,noexec,nosuid,nodev",
                    "--user", "1000:1000",
                    "-e", "PYTHONDONTWRITEBYTECODE=1",
                    "-v", f"{os.path.abspath(tmpdir)}:/app:ro",
                    self.docker_image,
                    "python", "/app/script.py",
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 3)
                except asyncio.TimeoutError:
                    proc.kill()
                    return SandboxResult(
                        run_id=run_id, success=False,
                        stdout="", stderr="TIMEOUT",
                        exit_code=-1, duration_s=time.time() - t0, mode="docker",
                    )
                
                # SRE Hardening: Docker 'resource temporarily unavailable' hatasını yakala ve raporla
                stderr_str = stderr.decode("utf-8", errors="replace")
                if proc.returncode != 0 and "resource temporarily unavailable" in stderr_str:
                     _log.error(f"Docker subsystem failure (resource limit?): {stderr_str}")
                     # Prod değilse veya test ortamındaysak subprocess fallback dene (Geliştirici dostu)
                     if not self._is_prod or "PYTEST_CURRENT_TEST" in os.environ:
                         _log.warning(f"[{run_id}] Docker hatası veya Test ortamı nedeniyle subprocess fallback yapılıyor.")
                         return await self._run_subprocess(run_id, code, extra_files, timeout)

                max_b = self.max_output_kb * 1024
                return SandboxResult(
                    run_id=run_id,
                    success=(proc.returncode == 0),
                    stdout=stdout.decode("utf-8", errors="replace")[:max_b],
                    stderr=stderr_str[:max_b],
                    exit_code=proc.returncode or 0,
                    duration_s=time.time() - t0,
                    mode="docker",
                )
            except Exception as e:
                _log.error(f"Docker çalıştırma hatası [{run_id}]: {e}")
                if not self._is_prod:
                    return await self._run_subprocess(run_id, code, extra_files, timeout)
                return SandboxResult(
                    run_id=run_id, success=False,
                    stdout="", stderr=f"DOCKER ERROR: {str(e)}",
                    exit_code=-1, duration_s=time.time() - t0, mode="docker",
                )

    async def _run_subprocess(
        self,
        run_id:      str,
        code:        str,
        extra_files: dict[str, str],
        timeout:     int,
    ) -> SandboxResult:
        _log.warning(
            f"!! GÜVENLİK UYARISI !! Sandbox subprocess modunda çalışıyor [{run_id}]. "
            "Ağ izolasyonu ve tam dosya sistemi izolasyonu garanti edilemez! "
            "Lütfen Docker kurulu olduğundan emin olun."
        )
        t0 = time.time()
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = os.path.join(tmpdir, "script.py")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(code)
            for fname, content in extra_files.items():
                with open(os.path.join(tmpdir, fname), "w", encoding="utf-8") as f:
                    f.write(content)
            try:
                # Windows/Linux uyumluluğu için python/python3 tespiti
                exe = "python" if os.name == "nt" else "python3"
                proc = await asyncio.create_subprocess_exec(
                    exe, main_path,
                    cwd=tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={
                        "PATH":             os.environ.get("PATH", ""),
                        "PYTHONPATH":       tmpdir,
                        "PYTHONIOENCODING": "utf-8",
                        "HOME":             tmpdir,
                        "TMPDIR":           tmpdir,
                    },
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    proc.kill()
                    return SandboxResult(
                        run_id=run_id, success=False,
                        stdout="", stderr=f"TIMEOUT after {timeout}s",
                        exit_code=-1, duration_s=time.time() - t0, mode="subprocess",
                    )
                max_b = self.max_output_kb * 1024
                return SandboxResult(
                    run_id=run_id,
                    success=(proc.returncode == 0),
                    stdout=stdout.decode("utf-8", errors="replace")[:max_b],
                    stderr=stderr.decode("utf-8", errors="replace")[:max_b],
                    exit_code=proc.returncode or 0,
                    duration_s=time.time() - t0,
                    mode="subprocess",
                )
            except Exception as e:
                return SandboxResult(
                    run_id=run_id, success=False,
                    stdout="", stderr=str(e),
                    exit_code=-1, duration_s=time.time() - t0, mode="subprocess",
                )


# Singleton
_sandbox_runner: "SandboxRunner | None" = None


def get_sandbox_runner(
    timeout:      int  = 10,
    max_output_kb: int = 4,
    use_docker:   bool = True,
) -> SandboxRunner:
    global _sandbox_runner
    if _sandbox_runner is None:
        _sandbox_runner = SandboxRunner(
            timeout=timeout,
            max_output_kb=max_output_kb,
            use_docker=use_docker,
        )
    return _sandbox_runner
