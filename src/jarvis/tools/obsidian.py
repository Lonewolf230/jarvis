import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from rich.markdown import Markdown
from rich.console import Console

from jarvis.ingestion.ingester import Ingester
from jarvis.logger import setup_logger
from jarvis.guardrails import REDACTED
from jarvis.settings import settings
from jarvis.tools.tools import untrusted
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

# note path -> hash of the text the model last saw in full. replace needs the file unchanged since then.
# shortcut: one dict per process, not per thread, and a restart forgets it; key it by thread_id once checkpointing is in
_read: dict[Path, str] = {}

def _digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_note(name: str, start: int = 0, end: int | None = None) -> str:
    """
    Read a note. name is a path relative to the vault, e.g. 'study/rag.md'.
    Reads the whole note by default. To read one region, pass start and end as character offsets,
    e.g. the slice_start and slice_end of a search_documents hit (add some margin for context).
    """
    p = _safe(name)
    # bytes.decode, not read_text: the chunk offsets were made on undecoded line endings
    text = p.read_bytes().decode("utf-8")
    if len(text[start:end]) == len(text) <= 20_000:  # only a complete read counts, however end was spelled
        _read[p] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # shortcut: cut long reads at 20k chars, page through with start/end when notes get bigger
    # notes can hold clipped web text, so the model gets them tagged like any other untrusted input
    return untrusted("note", text[start:end][:20_000], path=name)

def write_note(name: str, content: str, mode: Literal["create", "append", "replace"]) -> str:
    """
    Write a markdown note. name is relative to the vault and must end in .md.
    mode 'create' makes a new note and fails if it already exists.
    mode 'append' adds content to the end of an existing note and fails if it is missing.
    mode 'replace' overwrites an existing note, erasing the old text, so send the full new text.
    It fails unless you read the note with read_note first.
    """
    p = _safe(name)
    if p.suffix != ".md":
        raise ValueError("notes must end in .md")
    if mode == "create":
        if p.exists():
            raise ValueError(f"{name} already exists: use append or replace")
        p.parent.mkdir(parents=True, exist_ok=True)
    elif not p.exists():
        raise ValueError(f"{name} does not exist: use create (or check the path with list_notes)")
    elif mode == "replace" and REDACTED in content:
        raise ValueError(f"{name} was shown with secrets redacted, so replace would overwrite them with {REDACTED}. Use append instead.")
    elif mode == "replace" and _read.get(p) != _digest(p):
        raise ValueError(f"read all of {name} with read_note before replacing it (it was not read in full, or it changed since)")
    content = re.sub(r"</?note\b[^>]*>\n?", "", content)  # read_note output is tagged; a model that copies it back must not save the tags
    with p.open("w" if mode in ("create", "replace") else "a", encoding="utf-8") as f:
        f.write(content)
    if mode != "append":
        _read[p] = _digest(p)  # the writer knows the new text, so a later replace is allowed
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
