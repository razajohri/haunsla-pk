from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import Job

DEMO_JOBS = [
    {
        "external_id": "demo-1",
        "title": "Senior React Native Engineer",
        "company": "Peak Labs",
        "description": "Build mobile experiences for a global remote-first product team. Async culture, overlap with PKT mornings preferred.",
        "apply_url": "https://example.com/jobs/react-native",
        "category": "tech",
        "experience_level": "senior",
        "job_type": "full-time",
        "salary_min": 60000,
        "salary_max": 90000,
        "tags": ["Remote", "Full-time", "Tech"],
        "source": "demo",
        "is_featured": True,
        "days_ago": 0,
    },
    {
        "external_id": "demo-2",
        "title": "Product Designer (UI/UX)",
        "company": "Naya Design",
        "description": "Own end-to-end design for a B2B SaaS product. Figma proficiency required. Fully remote across APAC/EMEA.",
        "apply_url": "https://example.com/jobs/designer",
        "category": "design",
        "experience_level": "mid",
        "job_type": "full-time",
        "salary_min": 40000,
        "salary_max": 65000,
        "tags": ["Remote", "Full-time", "Design"],
        "source": "demo",
        "days_ago": 1,
    },
    {
        "external_id": "demo-3",
        "title": "Content Writer — Tech Blog",
        "company": "WriteFlow",
        "description": "Write SEO-friendly articles for developer tools. Native English writing quality expected. Flexible hours.",
        "apply_url": "https://example.com/jobs/writer",
        "category": "writing",
        "experience_level": "entry",
        "job_type": "contract",
        "salary_min": 1500,
        "salary_max": 3000,
        "salary_currency": "USD",
        "tags": ["Remote", "Contract", "Writing"],
        "source": "demo",
        "days_ago": 2,
    },
    {
        "external_id": "demo-4",
        "title": "Customer Success Specialist",
        "company": "Supportly",
        "description": "Help SaaS customers succeed over chat and email. Excellent English + Urdu a plus. PKT business hours.",
        "apply_url": "https://example.com/jobs/support",
        "category": "support",
        "experience_level": "entry",
        "job_type": "full-time",
        "salary_min": 18000,
        "salary_max": 28000,
        "tags": ["Remote", "Full-time", "Support"],
        "source": "demo",
        "days_ago": 3,
    },
    {
        "external_id": "demo-5",
        "title": "Growth Marketing Manager",
        "company": "ScalePK",
        "description": "Lead performance marketing for a Pakistani remote-first startup hiring globally. Paid ads + lifecycle email.",
        "apply_url": "https://example.com/jobs/marketing",
        "category": "marketing",
        "experience_level": "mid",
        "job_type": "full-time",
        "salary_min": 35000,
        "salary_max": 55000,
        "tags": ["Remote", "Full-time", "Marketing"],
        "source": "demo",
        "is_featured": True,
        "days_ago": 1,
    },
    {
        "external_id": "demo-6",
        "title": "Freelance Bookkeeper",
        "company": "Ledger Lane",
        "description": "Part-time remote bookkeeping for US clients. QuickBooks experience preferred.",
        "apply_url": "https://example.com/jobs/finance",
        "category": "finance",
        "experience_level": "mid",
        "job_type": "freelance",
        "salary_min": 20,
        "salary_max": 35,
        "tags": ["Remote", "Freelance", "Finance"],
        "source": "demo",
        "days_ago": 5,
    },
]


def seed_demo_jobs() -> None:
    if Job.query.filter_by(source="demo").count() > 0:
        return

    now = datetime.now(timezone.utc)
    for item in DEMO_JOBS:
        days_ago = item.pop("days_ago", 0)
        job = Job(
            **item,
            is_remote=True,
            pakistan_friendly=True,
            posted_at=now - timedelta(days=days_ago),
        )
        db.session.add(job)
    db.session.commit()
