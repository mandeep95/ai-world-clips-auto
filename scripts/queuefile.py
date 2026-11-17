"""Read/write the per-account posting queue (YAML).

Queue item fields:
  id:           day number in the account's run (#8, #9, ...)
  index:        original download index (the -N- in the source file name)
  title:        short human title for the clip
  source:       file name inside the account's videos/ folder
  hook:         one short caption hook line (no "Kling"/"AI" wording)
  status:       pending | done | held | skipped
  posted_date:  YYYY-MM-DD, set when the item is posted
  urls:         {platform: live_url} for platforms that succeeded
  note:         free-text notes (flaws, decisions, history)
"""
import yaml


def load_queue(path):
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    items = data.get("items", [])
    for it in items:
        it.setdefault("urls", {})
        it.setdefault("status", "pending")
    return data


def next_pending(queue):
    """First item with status 'pending', in file order. Held/skipped stay put."""
    for it in queue.get("items", []):
        if it.get("status") == "pending":
            return it
    return None


def find_item(queue, item_id):
    for it in queue.get("items", []):
        if str(it.get("id")) == str(item_id):
            return it
    return None


def save_queue(path, queue):
    with open(path, "w") as f:
        yaml.safe_dump(queue, f, sort_keys=False, allow_unicode=True)
