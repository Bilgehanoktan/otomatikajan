def test_deliberate_dogfooding_bug():
    # This is a deliberate bug introduced for the dogfooding demo.
    # The self-repair system should detect this test failure,
    # create an audit finding, and enqueue a self-repair case.
    assert 1 == 2, "Deliberate failure for Dogfooding Demo"
