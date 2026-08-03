from ats_location import is_pakistan_job_row


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


def test_rejects_us_location_even_if_description_says_global_strategy():
    assert not is_pakistan_job_row(
        {
            "title": "Programs Manager",
            "company": "Airbnb",
            "location": "New York, United States",
            "description": "This role translates global strategy into regional execution.",
            "is_remote": True,
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


def test_rejects_remote_us_slug():
    assert not is_pakistan_job_row(
        {
            "title": "Engineer",
            "company": "Acme",
            "location": "Remote-US",
            "description": "Build APIs",
            "is_remote": True,
        }
    )


def test_rejects_india_office_remote_label():
    assert not is_pakistan_job_row(
        {
            "title": "Supervisor",
            "company": "Acme",
            "location": "Gurugram, India",
            "description": "Remote-friendly team in India",
            "is_remote": True,
        }
    )


def test_rejects_remote_in_the_us():
    assert not is_pakistan_job_row(
        {
            "title": "Marketing Manager",
            "company": "Stripe",
            "location": "Remote in the US",
            "description": "Remote role",
            "is_remote": True,
        }
    )


def test_rejects_remote_uae():
    assert not is_pakistan_job_row(
        {
            "title": "Solutions Architect - MENA",
            "company": "Gitlab",
            "location": "Remote, UAE",
            "description": "Remote in MENA",
            "is_remote": True,
        }
    )


def test_rejects_remote_colombia():
    assert not is_pakistan_job_row(
        {
            "title": "Software Engineer",
            "company": "Twilio",
            "location": "Remote - Colombia",
            "description": "Remote engineering",
            "is_remote": True,
        }
    )
