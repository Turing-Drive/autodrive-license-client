#!/usr/bin/env python3
# collect_hwid.py — generate a license request JSON (no MACs)
import argparse, hashlib, json, os, re, time
from pathlib import Path

def read_first_line(p: str) -> str:
    try:
        with open(p, "r") as f:
            s = f.readline().strip()
        return re.sub(r"\s+", "", s).lower()
    except Exception:
        return ""

def find_rootfs_uuid() -> str:
    root_dev = ""
    try:
        with open("/proc/self/mounts","r") as f:
            for line in f:
                dev, mntp, *_ = line.split()
                if mntp == "/":
                    root_dev = dev; break
    except Exception:
        pass
    if not root_dev: return ""
    byuuid = Path("/dev/disk/by-uuid")
    if not byuuid.exists(): return ""
    for entry in byuuid.iterdir():
        try:
            target = os.readlink(str(entry))
            full = os.path.join("/dev", target)
            if full == root_dev:
                return entry.name.lower()
        except OSError:
            continue
    return ""

def calc_components():
    parts = []
    mid = read_first_line("/etc/machine-id")
    if mid: parts.append(f"mid:{mid}")
    dmi_prod = read_first_line("/sys/class/dmi/id/product_uuid")
    if dmi_prod: parts.append(f"dmi:{dmi_prod}")
    dmi_board = read_first_line("/sys/class/dmi/id/board_serial")
    if dmi_board: parts.append(f"brd:{dmi_board}")
    fsu = find_rootfs_uuid()
    if fsu: parts.append(f"fs:{fsu}")
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

    # decide output filename
    if args.out:
        outname = args.out
    else:
        outname = f"license_request-{hwid[:12]}.json"

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
        },
    }
    with open(outname, "w") as f:
        json.dump(req, f, ensure_ascii=False, separators=(",",":"))
    print("wrote", outname)
    print("HWID:", hwid)

if __name__ == "__main__":
    main()
