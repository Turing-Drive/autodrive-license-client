#!/usr/bin/env python3
# collect_hwid.py — generate a license request JSON (no MACs)
import argparse, hashlib, json, os, re, sys, time, subprocess
from pathlib import Path

def read_first_line(p: str) -> str:
    """Read first line, strip whitespace, lower-case, and remove inner spaces."""
    try:
        with open(p, "r") as f:
            s = f.readline().strip()
        return re.sub(r"\s+", "", s).lower()
    except Exception:
        return ""

def read_all(p: str) -> str:
    """Read entire file as text; return empty string on error."""
    try:
        return Path(p).read_text()
    except Exception:
        return ""

_KEEP_FLAGS = {"sse2", "sse4_2", "avx", "avx2", "avx512f"}

def parse_cpuinfo():
    """Parse /proc/cpuinfo (first processor block) into vendor/sig/isa-subset."""
    txt = read_all("/proc/cpuinfo")
    if not txt:
        return None
    vendor = family = model = stepping = ""
    flags = ""
    for line in txt.splitlines():
        if not line.strip():
            break
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = re.sub(r"\s+", "", k).lower()
        v = v.strip().lower()
        if k == "vendor_id":
            vendor = re.sub(r"\s+", "", v)
        elif k in ("cpufamily", "cpu family"):
            family = re.sub(r"\s+", "", v)
        elif k == "model":
            model = re.sub(r"\s+", "", v)
        elif k == "stepping":
            stepping = re.sub(r"\s+", "", v)
        elif k in ("flags", "features"):
            flags = v
    if not (vendor and family and model and stepping):
        return None
    present = sorted({t for t in re.split(r"\s+", flags) if t in _KEEP_FLAGS})
    isa = ",".join(present) if present else ""
    sig = f"{family}-{model}-{stepping}"
    return {"vendor": vendor, "sig": sig, "isa": isa}

_UUID_RE = re.compile(r"UUID:\s*(GPU-[A-Za-z0-9\-]+)", re.IGNORECASE)

def collect_gpu_uuids():
    """Return sorted unique list of NVIDIA GPU UUIDs (lower-case)."""
    uuids = []

    base = Path("/proc/driver/nvidia/gpus")
    if base.exists():
        for d in sorted(base.iterdir()):
            info = d / "information"
            try:
                for line in info.read_text().splitlines():
                    l = line.strip().lower()
                    if "gpu uuid:" in l:
                        p = l.find("gpu-")
                        if p >= 0:
                            uuids.append(l[p:])
            except Exception:
                continue

    if not uuids:
        try:
            out = subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.DEVNULL, text=True)
            for line in out.splitlines():
                m = _UUID_RE.search(line)
                if m:
                    uuids.append(m.group(1).lower())
        except Exception:
            pass

    uuids = sorted(sorted(set(uuids)))
    return uuids

def read_board_name():
    """Read DMI board_name (lower/trimmed, no inner spaces)."""
    s = read_first_line("/sys/class/dmi/id/board_name")
    return s

def calc_components():
    """
    Build a normalized, labeled component list. ALL three sources are required.
    If any source is missing, exit with error.
    """
    parts = []

    bn = read_board_name()
    if not bn:
        print("ERROR: missing DMI board_name (/sys/class/dmi/id/board_name)", file=sys.stderr)
        sys.exit(3)
    parts.append(f"brd:{bn}")

    ci = parse_cpuinfo()
    if not ci:
        print("ERROR: missing or unparsable /proc/cpuinfo", file=sys.stderr)
        sys.exit(3)
    parts.append(f"cpuv:{ci['vendor']}")
    parts.append(f"cpus:{ci['sig']}")
    if ci["isa"]:
        parts.append(f"cpui:{ci['isa']}")

    uuids = collect_gpu_uuids()
    if not uuids:
        print("ERROR: no NVIDIA GPU UUID found (need at least one GPU)", file=sys.stderr)
        sys.exit(3)
    parts.append("gpu:" + ";".join(uuids))

    parts.sort()
    return parts

def main():
    ap = argparse.ArgumentParser(description="Collect HWID for license request (no MACs).")
    ap.add_argument("--out", default="", help="Output filename (optional)")
    ap.add_argument("--features", nargs="*", default=["AutoDrive"], help="Requested features (optional)")
    ap.add_argument("--customer", default="", help="Customer label (optional)")
    args = ap.parse_args()

    parts = calc_components()
    hwid = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

    outname = args.out or f"license_request-{hwid[:12]}.json"

    req = {
        "version": 1,
        "timestamp": int(time.time()),
        "customer": args.customer,
        "features": sorted(args.features),
        "hwid_components": parts,
        "hwid_sha256": hwid,
        "env": {
            "uname": os.uname().sysname + " " + os.uname().release,
            "in_docker_hint": os.path.exists("/.dockerenv"),
            "gpu_count": len([*collect_gpu_uuids()]),
        },
    }
    with open(outname, "w") as f:
        json.dump(req, f, ensure_ascii=False, separators=(",",":"))
    print("wrote", outname)
    print("HWID:", hwid)

if __name__ == "__main__":
    main()
