"""Small examples used by the notebook workbench."""
PRESETS = {
    "Bell state · 12 gates to 2": (2, "H 0\nX 1\nX 1\nS 0\nSDG 0\nH 0\nH 0\nCX 0 1\nZ 1\nZ 1\nT 0\nTDG 0"),
    "Identity · cascading cancellation": (1, "H 0\nX 0\nX 0\nH 0"),
    "No redundant pairs": (2, "H 0\nCX 0 1\nT 1"),
    "Three-qubit GHZ state": (3, "H 0\nCX 0 1\nCX 1 2\nSWAP 0 2\nSWAP 2 0\nY 1\nY 1"),
}
