# test_classify.py
from scripts.classify import classify, Slot, Disposition

def test_locked_key_item():
    slot = Slot("trsr", {"index": 376}, item_id=374)
    rules = {"locked": [{"index": 376, "reason": "story key"}]}
    assert classify(slot, rules).disposition is Disposition.LOCKED

def test_unlisted_goes_to_pool():
    slot = Slot("trsr", {"index": 45}, item_id=32)
    assert classify(slot, {"locked": []}).disposition is Disposition.POOL

def test_forced_beats_null():
    slot = Slot("lvup", {"character": "Sora", "level": 1}, item_id=0)
    rules = {"exclude_null": True,
             "forced": [{"character": "Sora", "level": 1, "item": 372}]}
    d = classify(slot, rules)
    assert d.disposition is Disposition.FORCED and d.forced_item == 372