# 1. Filter — only what matters for move week
locked = [c for c in db["contacts"] if c["status"] == "LOCKED"]
shortlisted = [c for c in db["contacts"] if c["status"] == "shortlisted"]

# 2. Strip sensitive before pushing to PUBLIC room.html
# Keys to REMOVE for public commit:
STRIP_KEYS = ["phone", "phone_alt", "deposit_amount", "aadhaar_verified"]

public = [{k:v for k,v in c.items() if k not in STRIP_KEYS} for c in locked]

# 3. Desktop-critical columns — Builder must add these to notebook:
# desktop_allowed (bool), table_size (3x2 ft), ups_allowed (bool), earthing_ok (bool)
desktop_ready = [c for c in locked if c.get("desktop_allowed") and c.get("ups_allowed")]

# 4. Export
atomic_save(public, "radio/move_manifest.json") # for Bridge #fodi-boat-data
# HTML manifest for offline viewing on desktop without internet
