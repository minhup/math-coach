from app.scripts.seed_dev import milestone_five_device_invites


def test_milestone_five_device_invites_are_unique_and_clearly_synthetic() -> None:
    invites = milestone_five_device_invites()

    assert [code for code, _display_name in invites] == [
        "MATH-COACH-M5-COMPACT",
        "MATH-COACH-M5-PIXEL-7",
        "MATH-COACH-M5-IPHONE-13",
        "MATH-COACH-M5-IPAD-PORTRAIT",
        "MATH-COACH-M5-IPAD-LANDSCAPE",
    ]
    assert len({code for code, _display_name in invites}) == 5
    assert all("Synthetic" in display_name for _code, display_name in invites)
