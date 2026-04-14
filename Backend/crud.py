from __future__ import annotations
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Alert, AlertSeverity, AlertType, Branch, BranchStatus, Incident, Metric
from schemas import AlertCreate, IncidentCreate, MetricCreate

CITY_LOCALITIES: dict[str, list[str]] = {
    "Ahmedabad": [
        "Navrangpura", "Maninagar", "Bopal", "Satellite", "Vastrapur", "Naranpura", "Paldi",
        "Chandkheda", "Nikol", "Gota", "Thaltej", "Vejalpur", "Bapunagar", "Shahibaug",
        "Naroda", "Prahlad Nagar", "Sabarmati", "Isanpur", "CTM", "Khodiyar",
    ],
    "Pune": [
        "Shivajinagar", "Kothrud", "Hadapsar", "Wakad", "Aundh", "Baner", "Pimpri",
        "Chinchwad", "Kharadi", "Magarpatta", "Viman Nagar", "Warje", "Sinhagad Road",
        "Kondhwa", "Camp", "Deccan", "Karve Nagar", "Pashan", "Bavdhan", "Hinjewadi",
    ],
    "Mehsana": [
        "Radhanpur Road", "Modhera Road", "Rajmahal Road", "Highway Circle", "Palavasna",
        "Brahmanwada", "Unjha Road", "Station Road", "GIDC", "Nagalpur", "Sardar Chowk",
        "Lakhvad", "Jotana", "Kadi Gate", "Vijapur Road",
    ],
    "Rajkot": [
        "Kalawad Road", "Yagnik Road", "University Road", "Race Course", "Raiya", "150 Feet Ring Road",
        "Mavdi", "Aji Dam", "Bhakti Nagar", "Nana Mava", "Kuvadava Road", "Jamnagar Road",
        "Gondal Road", "Astron", "Trikon Baug", "Shapar", "Morbi Road", "Greenland Chowk",
    ],
    "Surat": [
        "Adajan", "Vesu", "Varachha", "Katargam", "Udhna", "Athwa", "Piplod", "Pal",
        "Parvat Patiya", "Pandesara", "Sachin", "Dumas Road", "Amroli", "Rander", "Bhatar",
        "Ring Road", "Nanpura", "Althan", "Majura", "Kapodara",
    ],
    "Valsad": [
        "Abrama", "Tithal Road", "Mograwadi", "Halar", "Atul", "GIDC", "Parnera",
        "Dharampur Road", "Gundlav", "Pardi Gate", "Vapi Road", "Hanuman Bhagda",
    ],
    "Himmatnagar": [
        "Mahavirnagar", "Motipura", "Khed Tasiya Road", "Station Road", "Panpur Patiya",
        "Sahakari Jin", "GIDC", "Berna", "Talod Road", "Idar Road", "Civil Circle",
    ],
    "Mumbai": [
        "Andheri", "Borivali", "Dadar", "Ghatkopar", "Mulund", "Chembur", "Kurla", "Bandra",
        "Malad", "Kandivali", "Worli", "Lower Parel", "Vikhroli", "Powai", "Santacruz",
        "Jogeshwari", "Byculla", "Colaba", "Sion", "Matunga",
    ],
    "Vasai": [
        "Vasai West", "Vasai East", "Nalasopara", "Naigaon", "Evershine", "Ambadi Road",
        "Bhabola", "Waliv", "Sativali", "Papdi", "Gokhivare", "Vasai Road",
    ],
    "Dombivli": [
        "Dombivli East", "Dombivli West", "MIDC", "Manpada", "Thakurli", "Tilak Nagar",
        "Phadke Road", "Shastri Nagar", "Ganesh Nagar", "Kopar", "Pandurangwadi",
    ],
    "Nagpur": [
        "Sitabuldi", "Dharampeth", "Pratap Nagar", "Manish Nagar", "Sadar", "Hingna",
        "Wardha Road", "Trimurti Nagar", "Itwari", "Mankapur", "Besa", "Nandanvan",
        "Jaripatka", "Katol Road", "Civil Lines",
    ],
    "Akola": [
        "Civil Lines", "Ramdaspeth", "Old City", "Gorakshan Road", "Murtizapur Road",
        "SBI Colony", "MIDC", "Telhara Naka", "Shastri Nagar", "Station Road",
    ],
    "Sangli": [
        "Vishrambag", "Madhavnagar", "Kupwad", "Miraj Road", "Station Chowk", "Market Yard",
        "Civil Hospital Area", "Wanlesswadi", "Haripur Road", "Shivaji Nagar",
    ],
    "Jalgaon": [
        "Ring Road", "Shivaji Nagar", "Ganesh Colony", "MIDC", "Station Road", "Raver Naka",
        "Pimprala", "Ajantha Chowk", "Muktainagar Road", "Bhusawal Naka",
    ],
    "Solapur": [
        "Jule Solapur", "Hotgi Road", "Saat Rasta", "Vijapur Road", "Akkalkot Road",
        "Railway Lines", "Datta Chowk", "Siddheshwar Peth", "Murarji Peth", "Mangalwar Peth",
    ],
    "Kalyan": [
        "Kalyan West", "Kalyan East", "Khadakpada", "Birla College", "Shivaji Chowk", "Kolsewadi",
        "Patri Pool", "Godrej Hill", "Pisavali", "Wayle Nagar", "Bail Bazar",
    ],
    "Hyderabad": [
        "Ameerpet", "Kukatpally", "Madhapur", "Gachibowli", "Begumpet", "Secunderabad", "Dilsukhnagar",
        "LB Nagar", "Miyapur", "Uppal", "Somajiguda", "Himayatnagar", "Banjara Hills", "Jubilee Hills",
        "Mehdipatnam", "Abids", "Nampally", "Kompally", "Manikonda", "Chandanagar",
    ],
    "Panipat": [
        "Model Town", "Insar Bazaar", "Tehsil Camp", "Sector 13", "Sector 25", "GT Road",
        "Huda", "Sanoli Road", "Assandh Road", "Babarpur", "Kaccha Camp",
    ],
    "Delhi": [
        "Karol Bagh", "Laxmi Nagar", "Rohini", "Dwarka", "Janakpuri", "Pitampura", "Paschim Vihar",
        "Connaught Place", "Nehru Place", "Rajouri Garden", "Saket", "Vasant Kunj", "Mayur Vihar",
        "Shahdara", "Narela", "Model Town", "Chandni Chowk", "Uttam Nagar", "Tilak Nagar", "Kalkaji",
    ],
}

COOPERATIVE_BANKS: list[dict[str, str]] = [
    {"name": "Ahmedabad District Cooperative Bank", "city": "Ahmedabad", "state": "Gujarat"},
    {"name": "Janata Sahakari Bank Ltd., Pune", "city": "Pune", "state": "Maharashtra"},
    {"name": "Kalupur Commercial Co-operative Bank Ltd.", "city": "Ahmedabad", "state": "Gujarat"},
    {"name": "Nutan Nagarik Sahakari Bank", "city": "Ahmedabad", "state": "Gujarat"},
    {"name": "Kalupur Commercial Co-operative Bank", "city": "Ahmedabad", "state": "Gujarat"},
    {"name": "Mehsana Urban Co-operative Bank", "city": "Mehsana", "state": "Gujarat"},
    {"name": "Rajkot Nagarik Sahakari Bank Ltd.", "city": "Rajkot", "state": "Gujarat"},
    {"name": "Surat People's Cooperative Bank Ltd.", "city": "Surat", "state": "Gujarat"},
    {"name": "Valsad District Cooperative Bank", "city": "Valsad", "state": "Gujarat"},
    {"name": "Sabarkantha District Cooperative Bank", "city": "Himmatnagar", "state": "Gujarat"},
    {"name": "Saraswat Cooperative Bank", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Abhyudaya Co-operative Bank Limited", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Cosmos Cooperative Bank", "city": "Pune", "state": "Maharashtra"},
    {"name": "Bharat Co-operative Bank (Mumbai) Ltd.", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Bassein Catholic Co-operative Bank Ltd.", "city": "Vasai", "state": "Maharashtra"},
    {"name": "Apna Sahakari Bank Ltd.", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Dombivli Nagari Sahakari Bank Ltd.", "city": "Dombivli", "state": "Maharashtra"},
    {"name": "Nagpur Nagarik Sahakari Bank", "city": "Nagpur", "state": "Maharashtra"},
    {"name": "Akola Urban Cooperative Bank", "city": "Akola", "state": "Maharashtra"},
    {"name": "Sangli Urban Co-operative Bank", "city": "Sangli", "state": "Maharashtra"},
    {"name": "Jalgaon Peoples Co-Operative Bank Ltd.", "city": "Jalgaon", "state": "Maharashtra"},
    {"name": "North Canara GSB Co-op Bank Ltd.", "city": "Mumbai", "state": "Maharashtra"},
    {"name": "Solapur Janata Sahakari Bank Ltd.", "city": "Solapur", "state": "Maharashtra"},
    {"name": "Pune Peoples Co-op Bank", "city": "Pune", "state": "Maharashtra"},
    {"name": "Kalyan Janata Sahakari Bank", "city": "Kalyan", "state": "Maharashtra"},
    {"name": "Andhra Pradesh Mahesh Co-operative Urban Bank", "city": "Hyderabad", "state": "Telangana"},
    {"name": "The Sutex Cooperative Bank Ltd.", "city": "Surat", "state": "Gujarat"},
    {"name": "Panipat Urban Cooperative Bank Ltd.", "city": "Panipat", "state": "Haryana"},
    {"name": "Delhi Nagrik Sehkari Bank Ltd.", "city": "Delhi", "state": "Delhi"},
    {"name": "Vasai Vikas Sahakari Bank", "city": "Vasai", "state": "Maharashtra"},
]

async def seed_database(session: AsyncSession) -> None:
    result = await session.execute(select(func.count(Branch.id)))
    branch_count = result.scalar_one() or 0
    if branch_count > 0:
        return

    for bank_index, bank in enumerate(COOPERATIVE_BANKS, start=1):
        bank_name = bank["name"]
        city = bank["city"]
        state = bank["state"]
        localities = CITY_LOCALITIES.get(city, [f"{city} Central", f"{city} Market", f"{city} East", f"{city} West"])

        max_branch_count = min(20, len(localities))
        min_branch_count = min(7, max_branch_count)
        num_branches = random.randint(min_branch_count, max_branch_count)
        selected_localities = random.sample(localities, k=num_branches)

        for branch_index, locality in enumerate(selected_localities, start=1):
            name = f"{bank_name} - {locality}, {city}"
            ip_address = f"10.{bank_index}.{branch_index}.11"

            branch = Branch(
                bank_name=bank_name,
                name=name,
                ip_address=ip_address,
                location=f"{city}, {state}",
                status=BranchStatus.healthy.value,
            )
            session.add(branch)
            await session.flush()

            session.add(
                Metric(
                    branch_id=branch.id,
                    cpu_usage=random.uniform(10.0, 45.0),
                    ram_usage=random.uniform(20.0, 60.0),
                    disk_usage=random.uniform(30.0, 75.0),
                    core_banking_service_up=True,
                    postgres_db_up=True,
                    network_up=True,
                )
            )

    await session.commit()

async def create_branch(session: AsyncSession, branch_data) -> Branch:
    branch = Branch(**branch_data.model_dump())
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch

async def get_branches(session: AsyncSession) -> list[Branch]:
    result = await session.execute(select(Branch).order_by(Branch.name))
    return list(result.scalars().all())

async def get_branch(session: AsyncSession, branch_id: int) -> Branch | None:
    result = await session.execute(select(Branch).where(Branch.id == branch_id))
    return result.scalar_one_or_none()

async def create_metric(session: AsyncSession, metric_data: dict) -> Metric:
    metric = Metric(**metric_data)
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric

async def get_latest_metrics(session: AsyncSession, branch_id: int, limit: int = 10) -> list[Metric]:
    result = await session.execute(
        select(Metric).where(Metric.branch_id == branch_id).order_by(Metric.recorded_at.desc()).limit(limit)
    )
    return list(result.scalars().all())

async def create_alert(session: AsyncSession, alert_data: AlertCreate) -> Alert:
    alert = Alert(
        branch_id=alert_data.branch_id,
        alert_type=alert_data.alert_type.value,
        message=alert_data.message,
        severity=alert_data.severity.value,
        is_resolved=False,
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert

async def resolve_alert(session: AsyncSession, alert: Alert) -> Alert:
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert

async def get_active_alerts(session: AsyncSession, branch_id: int | None = None) -> list[Alert]:
    query = select(Alert).where(Alert.is_resolved == False).order_by(Alert.fired_at.desc())
    if branch_id:
        query = query.where(Alert.branch_id == branch_id)
    result = await session.execute(query)
    return list(result.scalars().all())

async def create_incident(session: AsyncSession, incident_data: dict) -> Incident:
    incident = Incident(**incident_data)
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident

async def resolve_incident(session: AsyncSession, incident: Incident, auto_healed: bool) -> Incident:
    incident.auto_healed = auto_healed
    incident.resolved_at = datetime.now(timezone.utc)
    duration = incident.resolved_at - incident.started_at
    incident.duration_minutes = round(duration.total_seconds() / 60, 2)
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident

async def get_incidents(
    session: AsyncSession, 
    branch_id: int | None = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[Incident], int]:
    base_query = select(Incident)
    count_query = select(func.count(Incident.id))
    if branch_id:
        base_query = base_query.where(Incident.branch_id == branch_id)
        count_query = count_query.where(Incident.branch_id == branch_id)
    
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = base_query.order_by(Incident.started_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all()), total

async def ensure_branch_state(session: AsyncSession, branch: Branch) -> None:
    active_alerts = await get_active_alerts(session, branch.id)
    has_critical = any(a.severity == AlertSeverity.critical.value for a in active_alerts)
    has_warning = any(a.severity == AlertSeverity.warning.value for a in active_alerts)
    
    new_status = BranchStatus.healthy.value
    if has_critical:
        new_status = BranchStatus.critical.value
    elif has_warning:
        new_status = BranchStatus.warning.value
        
    if branch.status != new_status:
        branch.status = new_status
        session.add(branch)
        await session.commit()

async def generate_branch_metric(session: AsyncSession, branch: Branch) -> Metric:
    latest = await session.execute(
        select(Metric).where(Metric.branch_id == branch.id).order_by(Metric.recorded_at.desc()).limit(1)
    )
    last_metric = latest.scalar_one_or_none()

    if last_metric and branch.status == BranchStatus.critical.value:
        return last_metric

    base_cpu = 30.0 if not last_metric else last_metric.cpu_usage
    base_ram = 45.0 if not last_metric else last_metric.ram_usage
    base_disk = 50.0 if not last_metric else last_metric.disk_usage

    new_cpu = max(5.0, min(95.0, base_cpu + random.uniform(-5.0, 5.0)))
    new_ram = max(20.0, min(90.0, base_ram + random.uniform(-2.0, 2.0)))
    new_disk = max(10.0, min(99.0, base_disk + random.uniform(-0.1, 0.5)))

    core_up = last_metric.core_banking_service_up if last_metric else True
    db_up = last_metric.postgres_db_up if last_metric else True
    net_up = last_metric.network_up if last_metric else True

    # Random tiny chance of natural recovery if in warning
    if branch.status == BranchStatus.warning.value and random.random() < 0.1:
        new_cpu = max(10.0, base_cpu - 20.0)
        
    metric = await create_metric(session, {
        "branch_id": branch.id,
        "cpu_usage": round(new_cpu, 1),
        "ram_usage": round(new_ram, 1),
        "disk_usage": round(new_disk, 1),
        "core_banking_service_up": core_up,
        "postgres_db_up": db_up,
        "network_up": net_up,
    })

    # Avoid creating duplicate unresolved warning alerts for the same branch.
    active_alert_types: set[str] = set()
    if new_cpu > 80.0 or new_disk > 90.0:
        active_alert_types_result = await session.execute(
            select(Alert.alert_type).where(
                Alert.branch_id == branch.id,
                Alert.is_resolved.is_(False),
                Alert.alert_type.in_([AlertType.high_cpu.value, AlertType.disk_full.value]),
            )
        )
        active_alert_types = set(active_alert_types_result.scalars().all())

    # Alert logic
    if new_cpu > 80.0 and AlertType.high_cpu.value not in active_alert_types:
        await create_alert(session, AlertCreate(
            branch_id=branch.id, alert_type=AlertType.high_cpu,
            message=f"High CPU Usage detected: {new_cpu:.1f}%", severity=AlertSeverity.warning
        ))
    if new_disk > 90.0 and AlertType.disk_full.value not in active_alert_types:
        await create_alert(session, AlertCreate(
            branch_id=branch.id, alert_type=AlertType.disk_full,
            message=f"Disk Usage critical: {new_disk:.1f}%", severity=AlertSeverity.warning
        ))

    await ensure_branch_state(session, branch)
    return metric

async def simulate_branch_failure(session: AsyncSession, branch: Branch) -> tuple[Metric, Alert, Incident]:
    metric = await create_metric(session, {
        "branch_id": branch.id,
        "cpu_usage": 100.0,
        "ram_usage": 98.5,
        "disk_usage": branch.metrics[0].disk_usage if branch.metrics else 65.0,
        "core_banking_service_up": False,
        "postgres_db_up": True,
        "network_up": True,
    })

    alert = await create_alert(session, AlertCreate(
        branch_id=branch.id,
        alert_type=AlertType.service_down,
        message="Core Banking Service is DOWN (Simulated Failure)",
        severity=AlertSeverity.critical
    ))

    incident = await create_incident(session, {
        "branch_id": branch.id,
        "alert_id": alert.id,
        "description": "core-banking service crashed and requires auto-heal",
        "auto_healed": False,
        "heal_action": "Restarted core-banking-svc via Ansible auto-heal", # Prepared
    })

    await ensure_branch_state(session, branch)
    return metric, alert, incident

async def heal_branch(session: AsyncSession, branch: Branch) -> tuple[Metric, Alert | None, Incident | None]:
    latest_metrics = await get_latest_metrics(session, branch.id, limit=2)
    last_disk = latest_metrics[0].disk_usage if latest_metrics else 60.0

    healed_metric = await create_metric(session, {
        "branch_id": branch.id,
        "cpu_usage": random.uniform(25.0, 40.0),
        "ram_usage": random.uniform(40.0, 55.0),
        "disk_usage": last_disk,
        "core_banking_service_up": True,
        "postgres_db_up": True,
        "network_up": True,
    })

    alerts = await get_active_alerts(session, branch.id)
    resolved_alert = None
    for a in alerts:
        resolved_alert = await resolve_alert(session, a)

    incidents_query = select(Incident).where(
        and_(Incident.branch_id == branch.id, Incident.resolved_at == None)
    ).order_by(Incident.started_at.desc())
    open_incidents = await session.execute(incidents_query)
    
    resolved_incident = None
    for open_incident in open_incidents.scalars().all():
        resolved_incident = await resolve_incident(session, open_incident, auto_healed=True)
        
    branch.status = BranchStatus.healthy.value
    session.add(branch)
    await session.commit()
    
    return healed_metric, resolved_alert, resolved_incident
