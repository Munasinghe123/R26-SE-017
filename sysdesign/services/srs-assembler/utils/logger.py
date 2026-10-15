import sys
from datetime import datetime

# Guarantee UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from rich.console import Console
    console = Console(highlight=False, soft_wrap=True)
    HAS_RICH = True
except Exception:
    HAS_RICH = False


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_banner(title: str):
    if HAS_RICH:
        console.print(f"\n[bold cyan]{'=' * 68}[/bold cyan]")
        console.print(f"[bold cyan]🚀 {title}[/bold cyan]")
        console.print(f"[bold cyan]{'=' * 68}[/bold cyan]")
    else:
        print(f"\n{'=' * 68}", flush=True)
        print(f"=== {title} ===", flush=True)
        print(f"{'=' * 68}", flush=True)


def log_request_received(job_id: str, project_name: str, model: str, num_fr: int, num_nfr: int, has_hld: bool, has_lld: bool, has_ui: bool):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}] [bold magenta]📥 [INCOMING REQUEST][/bold magenta] Job: [bold white]{job_id}[/bold white] | Project: [bold white]{project_name}[/bold white]")
        console.print(f"           Model: [yellow]{model}[/yellow] | Inputs: [green]{num_fr} FRs[/green], [green]{num_nfr} NFRs[/green]")
        console.print(f"           Annexes: HLD=[{'green' if has_hld else 'dim'}]{has_hld}[/], LLD=[{'green' if has_lld else 'dim'}]{has_lld}[/], UI=[{'green' if has_ui else 'dim'}]{has_ui}[/]")
    else:
        print(f"[{ts}] [INCOMING REQUEST] Job: {job_id} | Project: {project_name} | Model: {model} | Inputs: {num_fr} FRs, {num_nfr} NFRs | Annexes: HLD={has_hld}, LLD={has_lld}, UI={has_ui}", flush=True)


def log_stage_start(step: int, total: int, stage_name: str, details: str = ""):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}] [bold blue]⚙️  [STAGE {step}/{total}: {stage_name.upper()}][/bold blue] Generating... {details}")
    else:
        print(f"[{ts}] [STAGE {step}/{total}: {stage_name.upper()}] Generating... {details}", flush=True)


def log_stage_llm_done(stage_name: str, latency_ms: float, input_tokens: int | None, output_tokens: int | None):
    ts = _timestamp()
    lat_str = f"{latency_ms:.0f}ms" if latency_ms else "N/A"
    tok_str = f"in: {input_tokens or 0}, out: {output_tokens or 0}"
    if HAS_RICH:
        console.print(f"[{ts}]    [dim]↳ LLM call finished in [bold]{lat_str}[/bold] ({tok_str})[/dim]")
    else:
        print(f"[{ts}]    ↳ LLM call finished in {lat_str} ({tok_str})", flush=True)


def log_stage_validation(stage_name: str, passed: bool, passed_checks: int, total_checks: int, errors: list = None, warnings: list = None):
    ts = _timestamp()
    if passed:
        if HAS_RICH:
            console.print(f"[{ts}]    [bold green]✓ Validation Passed[/bold green] ({passed_checks}/{total_checks} deterministic checks)")
        else:
            print(f"[{ts}]    ✓ Validation Passed ({passed_checks}/{total_checks} deterministic checks)", flush=True)
    else:
        err_count = len(errors or [])
        if HAS_RICH:
            console.print(f"[{ts}]    [bold red]✗ Validation Failed[/bold red] ({err_count} errors, {passed_checks}/{total_checks} checks passed)")
            for err in (errors or [])[:3]:
                msg = err.get("message", str(err))
                console.print(f"       [red]• {msg}[/red]")
        else:
            print(f"[{ts}]    ✗ Validation Failed ({err_count} errors)", flush=True)
            for err in (errors or [])[:3]:
                print(f"       • {err.get('message', str(err))}", flush=True)


def log_repair_start(stage_name: str, attempt: int, max_attempts: int, error_count: int):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}] [bold yellow]🔧 [SELF-REPAIR: {stage_name.upper()}][/bold yellow] Attempt [bold]{attempt}/{max_attempts}[/bold] — resolving {error_count} validation error(s)...")
    else:
        print(f"[{ts}] [SELF-REPAIR: {stage_name.upper()}] Attempt {attempt}/{max_attempts} — resolving {error_count} validation error(s)...", flush=True)


def log_repair_result(stage_name: str, attempt: int, success: bool, latency_ms: float = 0):
    ts = _timestamp()
    lat_str = f"{latency_ms:.0f}ms" if latency_ms else ""
    if success:
        if HAS_RICH:
            console.print(f"[{ts}]    [bold green]✓ Self-Repair Succeeded[/bold green] (Attempt {attempt}) {lat_str}")
        else:
            print(f"[{ts}]    ✓ Self-Repair Succeeded (Attempt {attempt}) {lat_str}", flush=True)
    else:
        if HAS_RICH:
            console.print(f"[{ts}]    [bold red]✗ Self-Repair Incomplete[/bold red] (Attempt {attempt})")
        else:
            print(f"[{ts}]    ✗ Self-Repair Incomplete (Attempt {attempt})", flush=True)


def log_compiling_markdown(project_name: str, has_hld: bool, has_lld: bool, has_ui: bool):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}] [bold cyan]📑 [SRS COMPILER][/bold cyan] Rendering full IEEE 29148 Markdown specification...")
        console.print(f"           Sections: [dim]1. Scope | 2. Context | 3. Functional Req | 4. NFRs (ISO 25010) | 5. RTM[/dim]")
        console.print(f"           Annexes:  [dim]A. HLD Architecture ({has_hld}) | B. LLD Data/Class ({has_lld}) | C. UI Specs ({has_ui})[/dim]")
    else:
        print(f"[{ts}] [SRS COMPILER] Rendering full IEEE 29148 Markdown specification...", flush=True)
        print(f"           Sections: 1. Scope | 2. Context | 3. Functional Req | 4. NFRs | 5. RTM", flush=True)
        print(f"           Annexes:  A. HLD ({has_hld}) | B. LLD ({has_lld}) | C. UI ({has_ui})", flush=True)


def log_assembly_complete(status: str, total_tokens: int | None, total_latency_ms: float, pdf_path: str = None):
    ts = _timestamp()
    status_color = "green" if status == "valid" else ("yellow" if status == "invalid" else "red")
    lat_sec = f"{total_latency_ms / 1000.0:.1f}s" if total_latency_ms else "N/A"
    if HAS_RICH:
        console.print(f"\n[{ts}] [bold {status_color}]✨ [SRS GENERATION COMPLETE][/bold {status_color}] Status: [bold {status_color}]{status.upper()}[/bold {status_color}] | Total Time: [bold]{lat_sec}[/bold] | Tokens: [bold]{total_tokens or 'N/A'}[/bold]")
        if pdf_path:
            console.print(f"           [bold cyan]📄 PDF Compiled:[/bold cyan] [underline]{pdf_path}[/underline]")
        console.print(f"[bold cyan]{'-' * 68}[/bold cyan]\n")
    else:
        print(f"\n[{ts}] [SRS GENERATION COMPLETE] Status: {status.upper()} | Total Time: {lat_sec} | Tokens: {total_tokens or 'N/A'}", flush=True)
        if pdf_path:
            print(f"           PDF Compiled: {pdf_path}", flush=True)
        print("-" * 68 + "\n", flush=True)


def log_startup(port: int, model: str):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"\n[bold green]{'=' * 68}[/bold green]")
        console.print(f"[bold green]🌟 [SRS ASSEMBLER AGENT] ONLINE on port [bold white]{port}[/bold white][/bold green]")
        console.print(f"[{ts}] Model: [bold yellow]{model}[/bold yellow] | Engine: [bold cyan]LangGraph + Deterministic Self-Repair[/bold cyan]")
        console.print(f"[{ts}] Endpoints: [cyan]POST /run[/cyan] | [cyan]GET /download-pdf/{{job_id}}[/cyan] | [cyan]GET /health[/cyan]")
        console.print(f"[bold green]{'=' * 68}[/bold green]\n")
    else:
        print(f"\n{'=' * 68}", flush=True)
        print(f"=== [SRS ASSEMBLER AGENT] ONLINE on port {port} ===", flush=True)
        print(f"[{ts}] Model: {model} | Engine: LangGraph + Deterministic Self-Repair", flush=True)
        print(f"[{ts}] Endpoints: POST /run | GET /download-pdf/{{job_id}} | GET /health", flush=True)
        print(f"{'=' * 68}\n", flush=True)


def log_pdf_download(job_id: str, path: str = None):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}] [bold cyan]📥 [PDF DOWNLOAD][/bold cyan] Job: [bold white]{job_id}[/bold white] -> Serving [underline]{path or 'file'}[/underline]")
    else:
        print(f"[{ts}] [PDF DOWNLOAD] Job: {job_id} -> Serving {path or 'file'}", flush=True)


def log_stage_error(stage_name: str, error_type: str, message: str):
    ts = _timestamp()
    if HAS_RICH:
        console.print(f"[{ts}]    [bold red]❌ [{stage_name.upper()} ERROR - {error_type}]:[/bold red] {message}")
    else:
        print(f"[{ts}]    ❌ [{stage_name.upper()} ERROR - {error_type}]: {message}", flush=True)

