"""
Seed the jobs board with curated listings from well-known IT companies.

These are placeholder/dummy entries (source='seed') that link to each
company's real careers page. Safe to re-run — entries are upserted by
(source='seed', source_id). Replace or delete later from the admin panel,
or let the scheduled Remotive fetch add live listings alongside these.

Run inside the backend container:  python seed_jobs.py
"""

from datetime import datetime, timezone

from app.database import SessionLocal, engine, Base
from app.models import Job, generate_slug

SOURCE = "seed"

SEED = [
    {
        "key": "google-swe", "title": "Software Engineer III", "company": "Google",
        "location": "Bengaluru, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["C++", "Python", "Distributed Systems"],
        "apply_url": "https://www.google.com/about/careers/applications/jobs/results/",
        "company_logo": "https://logo.clearbit.com/google.com",
        "description": "<p>Design, develop, test, deploy and maintain large-scale software systems at Google. Work across the full stack on products used by billions.</p>",
    },
    {
        "key": "microsoft-senior-swe", "title": "Senior Software Engineer", "company": "Microsoft",
        "location": "Hyderabad, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["C#", ".NET", "Azure"],
        "apply_url": "https://careers.microsoft.com/v2/global/en/home.html",
        "company_logo": "https://logo.clearbit.com/microsoft.com",
        "description": "<p>Build cloud-scale services on Azure. Own features end-to-end, from design through deployment and operations.</p>",
    },
    {
        "key": "amazon-sde2", "title": "Software Development Engineer II", "company": "Amazon",
        "location": "Bengaluru, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["Java", "AWS", "Microservices"],
        "apply_url": "https://www.amazon.jobs/en/",
        "company_logo": "https://logo.clearbit.com/amazon.com",
        "description": "<p>Build and scale distributed systems that power Amazon's retail and AWS platforms. Deliver customer-obsessed software with high ownership.</p>",
    },
    {
        "key": "meta-swe-product", "title": "Software Engineer, Product", "company": "Meta",
        "location": "Remote", "remote": True, "job_type": "Full-time",
        "category": "software-dev", "tags": ["React", "GraphQL", "PHP"],
        "apply_url": "https://www.metacareers.com/jobs",
        "company_logo": "https://logo.clearbit.com/meta.com",
        "description": "<p>Ship consumer product features across Meta's family of apps. Collaborate with design and data to move key metrics.</p>",
    },
    {
        "key": "nvidia-dl", "title": "Deep Learning Engineer", "company": "NVIDIA",
        "location": "Pune, India", "remote": False, "job_type": "Full-time",
        "category": "data", "tags": ["PyTorch", "CUDA", "Machine Learning"],
        "apply_url": "https://www.nvidia.com/en-us/about-nvidia/careers/",
        "company_logo": "https://logo.clearbit.com/nvidia.com",
        "description": "<p>Develop and optimize deep learning models and GPU-accelerated pipelines. Push the state of the art in AI performance.</p>",
    },
    {
        "key": "ibm-cloud", "title": "Cloud Engineer", "company": "IBM",
        "location": "Bengaluru, India", "remote": False, "job_type": "Full-time",
        "category": "devops", "tags": ["Kubernetes", "Terraform", "Cloud"],
        "apply_url": "https://www.ibm.com/careers/search",
        "company_logo": "https://logo.clearbit.com/ibm.com",
        "description": "<p>Design and operate resilient cloud infrastructure for enterprise clients on IBM Cloud and hybrid platforms.</p>",
    },
    {
        "key": "tcs-fullstack", "title": "Full Stack Developer", "company": "Tata Consultancy Services",
        "location": "Chennai, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["Angular", "Node.js", "SQL"],
        "apply_url": "https://www.tcs.com/careers",
        "company_logo": "https://logo.clearbit.com/tcs.com",
        "description": "<p>Build web applications for global enterprise clients across the full stack, from UI to database.</p>",
    },
    {
        "key": "infosys-systems", "title": "Systems Engineer", "company": "Infosys",
        "location": "Bengaluru, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["Java", "Spring", "REST"],
        "apply_url": "https://www.infosys.com/careers/",
        "company_logo": "https://logo.clearbit.com/infosys.com",
        "description": "<p>Join Infosys as a Systems Engineer working on enterprise application development and modernization projects.</p>",
    },
    {
        "key": "wipro-data", "title": "Data Engineer", "company": "Wipro",
        "location": "Hyderabad, India", "remote": False, "job_type": "Full-time",
        "category": "data", "tags": ["Spark", "Python", "ETL"],
        "apply_url": "https://careers.wipro.com/",
        "company_logo": "https://logo.clearbit.com/wipro.com",
        "description": "<p>Build and maintain data pipelines and warehouses that power analytics for enterprise customers.</p>",
    },
    {
        "key": "accenture-devops", "title": "DevOps Engineer", "company": "Accenture",
        "location": "Gurugram, India", "remote": False, "job_type": "Full-time",
        "category": "devops", "tags": ["CI/CD", "Docker", "AWS"],
        "apply_url": "https://www.accenture.com/in-en/careers",
        "company_logo": "https://logo.clearbit.com/accenture.com",
        "description": "<p>Automate build, test and deployment pipelines and manage cloud infrastructure for client engagements.</p>",
    },
    {
        "key": "adobe-frontend", "title": "Frontend Engineer", "company": "Adobe",
        "location": "Noida, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["React", "TypeScript", "CSS"],
        "apply_url": "https://careers.adobe.com/us/en",
        "company_logo": "https://logo.clearbit.com/adobe.com",
        "description": "<p>Craft delightful, performant web experiences for Adobe's creative and document products.</p>",
    },
    {
        "key": "salesforce-backend", "title": "Backend Engineer (Java)", "company": "Salesforce",
        "location": "Hyderabad, India", "remote": False, "job_type": "Full-time",
        "category": "software-dev", "tags": ["Java", "APIs", "Cloud"],
        "apply_url": "https://careers.salesforce.com/en/jobs/",
        "company_logo": "https://logo.clearbit.com/salesforce.com",
        "description": "<p>Build scalable backend services and APIs on the Salesforce platform used by enterprises worldwide.</p>",
    },
    {
        "key": "oracle-cloud", "title": "Cloud Solutions Engineer", "company": "Oracle",
        "location": "Bengaluru, India", "remote": False, "job_type": "Full-time",
        "category": "devops", "tags": ["OCI", "Linux", "Cloud"],
        "apply_url": "https://careers.oracle.com/",
        "company_logo": "https://logo.clearbit.com/oracle.com",
        "description": "<p>Design and deliver cloud solutions on Oracle Cloud Infrastructure for enterprise customers.</p>",
    },
    {
        "key": "sap-ml", "title": "Machine Learning Engineer", "company": "SAP",
        "location": "Bengaluru, India", "remote": True, "job_type": "Full-time",
        "category": "data", "tags": ["Python", "ML", "NLP"],
        "apply_url": "https://jobs.sap.com/",
        "company_logo": "https://logo.clearbit.com/sap.com",
        "description": "<p>Develop machine learning features embedded in SAP's enterprise software suite.</p>",
    },
    {
        "key": "cognizant-qa", "title": "QA Automation Engineer", "company": "Cognizant",
        "location": "Chennai, India", "remote": False, "job_type": "Full-time",
        "category": "qa", "tags": ["Selenium", "Python", "Automation"],
        "apply_url": "https://careers.cognizant.com/global/en",
        "company_logo": "https://logo.clearbit.com/cognizant.com",
        "description": "<p>Design and maintain automated test suites to ensure software quality across client projects.</p>",
    },
]


def run():
    # Ensure the jobs table exists (harmless if already created by the app).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    created = updated = 0
    now = datetime.now(timezone.utc)
    try:
        for item in SEED:
            key = item["key"]
            fields = {k: v for k, v in item.items() if k != "key"}
            existing = (
                db.query(Job)
                .filter(Job.source == SOURCE, Job.source_id == key)
                .first()
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                existing.published = True
                updated += 1
            else:
                job = Job(source=SOURCE, source_id=key, published=True,
                          pinned=False, posted_at=now, **fields)
                job.slug = generate_slug(f"{job.title} at {job.company}", db, Job)
                db.add(job)
                created += 1
            db.commit()
    finally:
        db.close()
    print(f"Seed complete — created {created}, updated {updated}")


if __name__ == "__main__":
    run()
