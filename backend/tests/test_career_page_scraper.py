from career_page_scraper import _detect_ats, _parse_html_job_links, load_career_page_companies


def test_loads_career_page_config():
    companies = load_career_page_companies()
    assert len(companies) >= 40
    names = {c["name"] for c in companies}
    assert "10Pearls" in names
    assert "i2c Inc" in names
    assert "GitLab" in names


def test_detect_greenhouse_embed():
    html = 'boards-api.greenhouse.io/v1/boards/10pearlsamerica/jobs'
    assert ("greenhouse", "10pearlsamerica") in _detect_ats(html)


def test_parse_applytojob_links():
    html = '''
    <a href="https://venturedive.applytojob.com/apply/6yA1hAbMr4/Senior-Data-AI-Architect">
      Senior Data &amp; AI Architect
    </a>
    '''
    links = _parse_html_job_links(html, "https://venturedive.applytojob.com/apply")
    assert any("Senior Data" in l["title"] for l in links)
