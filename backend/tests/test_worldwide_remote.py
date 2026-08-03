from worldwide_remote import is_worldwide_remote_row


def test_keeps_worldwide_location():
    assert is_worldwide_remote_row(
        {
            "title": "Engineer",
            "company": "Acme",
            "location": "Worldwide",
            "description": "Work from anywhere",
            "is_remote": True,
        }
    )


def test_keeps_bare_remote():
    assert is_worldwide_remote_row(
        {
            "title": "Designer",
            "company": "Acme",
            "location": "Remote",
            "description": "Fully remote team",
            "is_remote": True,
        }
    )


def test_rejects_remote_us():
    assert not is_worldwide_remote_row(
        {
            "title": "Engineer",
            "company": "Acme",
            "location": "Remote US",
            "description": "Remote in the United States",
            "is_remote": True,
        }
    )
