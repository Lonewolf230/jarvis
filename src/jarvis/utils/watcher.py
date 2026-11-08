'''
    Watches the Obsidian vault and keeps the index in step with edits made outside the agent.
    Run: uv run python watcher.py
'''
import time
from pathlib import Path
from threading import Lock, Timer

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from jarvis.logger import setup_logger
from jarvis.tools.obsidian import VAULT, reindex
from jarvis.utils.store import Store

logger = setup_logger('watcher')

DEBOUNCE = 2.0  # seconds; Obsidian autosaves in bursts, wait for the burst to end


def sync(p: Path) -> None:
    '''
        Brings the index in step with one note: reindex if it exists, delete its chunks if not.
    '''
    if p.exists():
        logger.info(reindex(p))
        return
    file_id = p.relative_to(VAULT).as_posix()
    store = Store()
    try:
        store.delete_file(file_id)
        logger.info(f"Deleted chunks of {file_id}")
    finally:
        store.close()


class Handler(FileSystemEventHandler):

    def __init__(self):
        self.timers: dict[Path, Timer] = {}
        self.lock = Lock()

    def _schedule(self, path: str) -> None:
        # resolve: the watcher may report a different spelling of the vault path than VAULT
        p = Path(path).resolve()
        # shortcut: folder moves/deletes are ignored, their notes stay indexed until each is touched; upgrade by deleting on a file_id prefix
        if p.suffix != ".md" or ".obsidian" in p.parts:
            return
        with self.lock:
            if p in self.timers:
                self.timers[p].cancel()
            self.timers[p] = Timer(DEBOUNCE, self._run, args=(p,))
            self.timers[p].start()

    def _run(self, p: Path) -> None:
        with self.lock:
            self.timers.pop(p, None)
        try:
            sync(p)
        except Exception as e:
            logger.error(f"Sync of {p} failed: {e}")

    def on_created(self, event):
        self._schedule(event.src_path)

    def on_modified(self, event):
        self._schedule(event.src_path)

    def on_deleted(self, event):
        self._schedule(event.src_path)

    def on_moved(self, event):  # a rename: drop the old path, index the new one
        self._schedule(event.src_path)
        self._schedule(event.dest_path)


if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Handler(), str(VAULT), recursive=True)
    observer.start()
    logger.info(f"Watching {VAULT}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
