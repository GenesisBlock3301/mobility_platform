from app.infra.rate_limit import FixedWindowLimiter


def test_limit_applies_per_client_and_resets_each_window():
    limiter = FixedWindowLimiter()
    assert [limiter.hit("a", "read", 2, now=0)[0] for _ in range(3)] == [True, True, False]
    assert limiter.hit("b", "read", 2, now=0)[0]
    assert limiter.hit("a", "read", 2, now=60)[0]


def test_key_count_is_capped_so_memory_stays_bounded():
    limiter = FixedWindowLimiter(max_keys=100)
    for i in range(100):
        assert limiter.hit(f"client-{i}", "read", 5, now=0)[0]
    # A flood of new clients in the same window is refused rather than stored.
    allowed, retry_after = limiter.hit("client-new", "read", 5, now=0)
    assert not allowed
    assert retry_after == 60
    assert len(limiter._counts) == 100
    # Existing clients keep working, and the next window starts empty.
    assert limiter.hit("client-1", "read", 5, now=0)[0]
    assert limiter.hit("client-new", "read", 5, now=60)[0]
