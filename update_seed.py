import re

with open("Backend/crud.py", "r") as f:
    text = f.read()

# Replace BRANCH_SEEDS with a dynamic generator in seed_database
new_seed_func = """
async def seed_database(session: AsyncSession) -> None:
    result = await session.execute(select(func.count(Branch.id)))
    branch_count = result.scalar_one() or 0
    if branch_count > 0:
        return

    BANKS = [
        "UrbanBank", "HDFC Bank", "ICICI Bank", "State Bank of India",
        "Axis Bank", "Kotak Mahindra", "IndusInd Bank", "Yes Bank",
        "Punjab National Bank", "Bank of Baroda", "Canara Bank", 
        "Union Bank of India", "IDFC First", "Federal Bank", 
        "South Indian Bank", "Standard Chartered", "Citibank", "HSBC"
    ]
    
    cities = ["Mumbai", "Pune", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Surat", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara"]

    for bank_name in BANKS[:16]:  # create 16 banks
        num_branches = random.randint(7, 14)
        for _ in range(num_branches):
            city = random.choice(cities)
            branch_id_str = f"{random.randint(100, 999)}"
            name = f"{bank_name} - {city} {branch_id_str}"
            
            ip_address = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            
            branch = Branch(
                bank_name=bank_name,
                name=name,
                ip_address=ip_address,
                location=f"{city}, India",
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
"""

# Replace the giant BRANCH_SEEDS list and the old seed_database
# It's from line 11 to line 230
text = re.sub(r'BRANCH_SEEDS = \[.*?\]\n\n\nasync def seed_database.*?await session\.commit\(\)\n', new_seed_func, text, flags=re.DOTALL)

with open("Backend/crud.py", "w") as f:
    f.write(text)

print("crud.py updated.")
