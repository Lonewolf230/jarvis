SENSITIVE = {
    "write_note",
    "web_search"
}

MODES = {
    "safe" : {"ask" : SENSITIVE},
    "auto" : {"ask" : set()},
    "read_only" : {"deny":{"write_note"}}
}

MODE_LIST = list(MODES.keys())