from experience_level import infer_experience_level, is_fresh_grad_friendly


def test_internship_title():
    assert (
        infer_experience_level(
            {"title": "Software Engineering Intern", "description": "", "is_remote": True},
            trust_existing=False,
        )
        == "internship"
    )


def test_mentor_interns_not_internship():
    # Senior roles often mention mentoring interns in the body
    assert (
        infer_experience_level(
            {
                "title": "Software Engineer 2",
                "description": "You will mentor interns and junior engineers.",
            },
            trust_existing=False,
        )
        != "internship"
    )


def test_entry_level_junior():
    assert (
        infer_experience_level(
            {
                "title": "Junior Frontend Developer",
                "description": "0-2 years experience",
                "is_remote": True,
            },
            trust_existing=False,
        )
        == "entry"
    )


def test_fresh_grad_friendly():
    assert is_fresh_grad_friendly(
        {"title": "Graduate Marketing Associate", "description": "training provided"}
    )


def test_senior_not_fresh():
    assert not is_fresh_grad_friendly(
        {"title": "Senior Staff Engineer", "description": "10+ years required"}
    )
