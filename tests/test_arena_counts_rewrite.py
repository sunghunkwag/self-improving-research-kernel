from shared.arena_manager import ArenaManager


def test_counts_reports_all_managed_arenas():
    manager = ArenaManager(master_seed=7)
    assert manager.counts() == {"cce": 0, "thdse": 0, "bridge": 0}

    manager.alloc_cce()
    manager.alloc_thdse()
    manager.alloc_bridge()
    manager.alloc_bridge()

    assert manager.counts() == {"cce": 1, "thdse": 1, "bridge": 2}
