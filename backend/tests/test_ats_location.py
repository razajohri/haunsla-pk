from ats_location import is_pakistan_job_row


def test_keeps_board_remote_even_with_country_in_location():
    assert is_pakistan_job_row(
        {
            "title": "Account Executive - Italy",
            "company": "Gitlab",
            "location": "Remote, Italy",
            "description": "Remote sales role",
            "is_remote": True,
        }
    )


def test_keeps_pakistan_remote():
    assert is_pakistan_job_row(
        {
            "title": "Remote Support Agent",
            "company": "Acme",
            "location": "Pakistan",
            "description": "Fully remote role for Pakistan",
            "is_remote": True,
        }
    )


def test_keeps_worldwide_remote():
    assert is_pakistan_job_row(
        {
            "title": "Backend Engineer",
            "company": "Globex",
            "location": "Remote — Worldwide",
            "description": "Work from anywhere",
            "is_remote": True,
        }
    )


def test_rejects_us_only():
    assert not is_pakistan_job_row(
        {
            "title": "Engineer",
            "company": "US Co",
            "location": "Remote, USA",
            "description": "US only. Must be located in the United States.",
            "is_remote": True,
        }
    )


def test_rejects_non_remote():
    assert not is_pakistan_job_row(
        {
            "title": "Office Manager",
            "company": "Local Co",
            "location": "Lahore",
            "description": "On-site in Gulberg",
            "is_remote": False,
        }
    )


def test_keeps_bare_remote_location():
    assert is_pakistan_job_row(
        {
            "title": "Support Specialist",
            "company": "Acme",
            "location": "Remote",
            "description": "Help customers over email.",
            "is_remote": True,
        }
    )
