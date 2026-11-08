from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from rich.markdown import Markdown
from rich.console import Console

from jarvis.ingestion.ingester import Ingester
from jarvis.logger import setup_logger
from jarvis.settings import settings
from jarvis.utils.store import Store

logger = setup_logger('obsidian')

VAULT = Path(settings.VAULT_DIR, settings.VAULT_NAME).expanduser().resolve()

def _safe(name: str) -> Path:
    """
    Resolves a vault-relative note name to a path, refusing anything outside the vault.
    """
    p = (VAULT / name).resolve()
    if not p.is_relative_to(VAULT):  # blocks ../ and absolute paths
        raise ValueError(f"{name} is outside the vault")
    return p

def list_notes() -> list[str]:
    """
    List all notes in the vault as paths relative to the vault, e.g. 'study/rag.md'.
    """
    VAULT.mkdir(parents=True, exist_ok=True)
    return [str(p.relative_to(VAULT)) for p in VAULT.rglob("*.md")
            if ".obsidian" not in p.parts]

def read_note(name: str) -> str:
    """
    Read a note. name is a path relative to the vault, e.g. 'study/rag.md'.
    """
    # shortcut: cut long notes at 20k chars, chunk them when notes get bigger
    return _safe(name).read_text(encoding="utf-8")[:20_000]

def write_note(name: str, content: str, mode: Literal["a", "r"] = "a") -> str:
    """
    Write a markdown note. name is relative to the vault and must end in .md.
    mode 'a' adds content to the end (creates the note if missing).
    mode 'r' replaces the whole note, erasing the old text, so send the full new text.
    """
    p = _safe(name)
    if p.suffix != ".md":
        raise ValueError("notes must end in .md")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a" if mode == "a" else "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"mode {mode} done: {name}")
    return f"mode {mode} done: {name};"

def reindex(p: Path) -> str:
    """
    Re-indexes one note after a write. The note on disk is the source of truth,
    so an indexing failure is reported but never undoes the write.
    """
    file_id = p.relative_to(VAULT).as_posix()
    st = p.stat()
    to_utc = lambda t: datetime.fromtimestamp(t, tz=timezone.utc)
    store = None
    try:
        logger.info(f"Re-indexing file : {p}")
        store = Store()
        n = Ingester(store).reindex(file_id, p.read_bytes(), to_utc(getattr(st, "st_birthtime", st.st_mtime)), to_utc(st.st_mtime))
        return f"indexed {n} chunks of {file_id}"
    except Exception as e:
        logger.error(f"Reindex of {file_id} failed: {e}")
        return "note saved but indexing failed, so it is not searchable yet"
    finally:
        if store:
            store.close()

def render_markdown(content: str) -> None:
    """
    Renders markdown content in the terminal.
    """
    console = Console()
    console.print(Markdown(content))
