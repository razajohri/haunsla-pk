from ats_location import is_pakistan_job_row
from pakistan_companies import load_pakistan_companies


def test_loads_many_pk_companies():
    companies = load_pakistan_companies()
    assert len(companies) >= 150
    names = {c["name"].lower() for c in companies}
    assert "habib bank limited" in names
    assert "systems limited" in names
    assert any("karachi" in [x.lower() for x in c["cities"]] for c in companies)
    assert any("lahore" in [x.lower() for x in c["cities"]] for c in companies)
    assert any("islamabad" in [x.lower() for x in c["cities"]] for c in companies)


def test_filter_keeps_lahore_local():
    assert is_pakistan_job_row(
        {
            "title": "Management Trainee",
            "company": "MCB Bank",
            "location": "Lahore, Pakistan",
            "description": "Fresh graduates welcome",
            "is_remote": False,
        }
    )


def test_filter_keeps_remote():
    assert is_pakistan_job_row(
        {
            "title": "Junior Developer",
            "company": "Remote Co",
            "location": "Remote",
            "description": "Worldwide",
            "is_remote": True,
        }
    )
