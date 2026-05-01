"""
Seed Script for BLW Cell Track Database
Populates Zone B (Cameroon) with realistic test data
Run once: python seed_database.py
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

# Import your models
from database import ASYNC_DATABASE_URL
from models import Base, Zone, Fellowship, SeniorCell, Cell, User, CellReport
from auth import hash_pin

load_dotenv()

# Setup async session
engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_database():
    """Populate database with test data"""
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: DROP ALL TABLES (HANDLE CIRCULAR DEPS)
    # ═══════════════════════════════════════════════════════════
    
    async with engine.begin() as conn:
        print("🗑️  Dropping existing tables...")
        
        # Drop in reverse order of dependencies
        await conn.execute(text("DROP TABLE IF EXISTS cell_reports CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS sync_queue CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS cells CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS senior_cells CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS fellowships CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS zones CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS regions CASCADE;"))
        
        print("✅ Tables dropped")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: RECREATE ALL TABLES
        # ═══════════════════════════════════════════════════════════
        
        print("🏗️  Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: POPULATE DATA
    # ═══════════════════════════════════════════════════════════
    
    async with AsyncSessionLocal() as session:
        print("\n🌱 Seeding Zone B (Cameroon)...\n")
        
        # ───────────────────────────────────────────────────────
        # CREATE ZONE B
        # ───────────────────────────────────────────────────────
        
        zone_b = Zone(
            name="Cameroon Zone B",
            location="Cameroon (Bamenda, Yaounde, Dschang, CAR, Eq. Guinea, Sao Tome)",
            description="BLW Cameroon Zone B : East & Central Africa Region"
        )
        session.add(zone_b)
        await session.flush()
        zone_b_id = zone_b.id
        print(f"✅ Zone B created: {zone_b_id}")
        
        # ───────────────────────────────────────────────────────
        # CREATE SYSTEM ADMIN (NO ZONE ASSIGNMENT)
        # ───────────────────────────────────────────────────────
        
        system_admin = User(
            phone="+237690000000",
            name="System Admin",
            pin_hash=hash_pin("123456"),
            role="system_admin",
            is_active=True
        )
        session.add(system_admin)
        await session.flush()
        print(f"✅ System Admin created: +237690000000 / 123456")
        
        # ───────────────────────────────────────────────────────
        # CREATE ZONAL ADMIN (ZONE ASSIGNED)
        # ───────────────────────────────────────────────────────
        
        zonal_admin = User(
            phone="+237690100001",
            name="Zonal Secretary : BLW Cameroon Zone B",
            pin_hash=hash_pin("123456"),
            role="zonal_admin",
            zone_id=zone_b_id,
            is_active=True
        )
        session.add(zonal_admin)
        await session.flush()
        print(f"✅ Zonal Admin created: +237690100001 / 123456\n")
        
        # ───────────────────────────────────────────────────────
        # CREATE FELLOWSHIPS (9 total)
        # ───────────────────────────────────────────────────────
        
        fellowships_data = [
            ("BLW University Of Bamenda", "Bambili, North West Region"),
            ("BLW National Polytechnic Yaounde", "Yaounde, Center Region"),
            ("BLW Siantou", "Yaounde, Center Region"),
            ("BLW University Of Dschang", "Dschang, West Region"),
            ("BLW National Polytechnic Bamenda", "Bamenda, North West Region"),
            ("CAR Mission", "Bangui, Central African Republic"),
            ("Equatorial Guinea", "Malabo, Equatorial Guinea"),
            ("Sao Tome Fellowship", "Sao Tome, Sao Tome & Principe"),
            ("Libreville Extension", "Libreville, Gabon"),
        ]
        
        fellowships = []
        for i, (name, location) in enumerate(fellowships_data):
            fellowship = Fellowship(
                name=name,
                location=location,
                zone_id=zone_b_id
            )
            session.add(fellowship)
            await session.flush()
            fellowships.append(fellowship)
            print(f"  ✅ Fellowship {i+1}: {name}")
        
        # ───────────────────────────────────────────────────────
        # CREATE FELLOWSHIP PASTORS (1 per fellowship)
        # ───────────────────────────────────────────────────────
        
        pastor_names = [
            "Pastor Stanley N",
            "Pastor Nelson Yembe",
            "Pastor David Siantou",
            "Pastor Grace Dschang",
            "Pastor Njini Rabiatu",
            "Pastor Che Titus",
            "Pastor Emmanuel Kevin",
            "Pastor Rebecca Sao Tome",
            "Pastor Michael Congo",
        ]
        
        print()
        for i, (fellowship, pastor_name) in enumerate(zip(fellowships, pastor_names)):
            pastor = User(
                phone=f"+237690200{i:03d}",
                name=pastor_name,
                pin_hash=hash_pin("123456"),
                role="fellowship_pastor",
                fellowship_id=fellowship.id,
                zone_id=zone_b_id,
                is_active=True
            )
            session.add(pastor)
            print(f"  ✅ Pastor: {pastor_name}")
        
        await session.flush()
        
        # ───────────────────────────────────────────────────────
        # CREATE SENIOR CELLS (2 per fellowship = 12 total)
        # ───────────────────────────────────────────────────────
        
        senior_cells = []
        senior_cl_count = 0
        
        print()
        for fellowship in fellowships[:6]:  # First 6 fellowships
            for j in range(2):
                division = chr(65 + j)  # A, B
                senior_cell = SeniorCell(
                    name=f"{fellowship.name} - Division {division}",
                    fellowship_id=fellowship.id
                )
                session.add(senior_cell)
                await session.flush()
                senior_cells.append(senior_cell)
                
                # Create senior cell leader
                senior_cl_count += 1
                senior_cl = User(
                    phone=f"+237690300{senior_cl_count:03d}",
                    name=f"Elder {chr(64 + senior_cl_count)} - {division}",
                    pin_hash=hash_pin("123456"),
                    role="senior_cell_leader",
                    senior_cell_id=senior_cell.id,
                    fellowship_id=fellowship.id,
                    zone_id=zone_b_id,
                    is_active=True
                )
                session.add(senior_cl)
                print(f"  ✅ Senior Cell: {senior_cell.name}")
        
        await session.flush()
        print(f"\n✅ {len(senior_cells)} Senior Cells + {senior_cl_count} Leaders created\n")
        
        # ───────────────────────────────────────────────────────
        # CREATE CELLS (6 per senior cell = 72 total)
        # ───────────────────────────────────────────────────────
        
        cells = []
        cell_leader_count = 0
        meeting_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        
        for senior_cell in senior_cells:
            for cell_num in range(1, 7):
                cell = Cell(
                    name=f"Cell {cell_num} - {senior_cell.name[:30]}",
                    senior_cell_id=senior_cell.id,
                    default_meeting_day=meeting_days[cell_num - 1],
                    meeting_time=None
                )
                session.add(cell)
                await session.flush()
                cells.append(cell)
                
                # Create cell leader
                cell_leader_count += 1
                cell_leader = User(
                    phone=f"+237690400{cell_leader_count:03d}",
                    name=f"Leader {cell_leader_count}",
                    pin_hash=hash_pin("123456"),
                    role="cell_leader",
                    cell_id=cell.id,
                    senior_cell_id=senior_cell.id,
                    fellowship_id=senior_cell.fellowship_id,
                    zone_id=zone_b_id,
                    is_active=True
                )
                session.add(cell_leader)
        
        await session.flush()
        print(f"✅ {len(cells)} Cells + {cell_leader_count} Cell Leaders created\n")
        
        # ───────────────────────────────────────────────────────
        # CREATE SAMPLE REPORTS (30 cells with reports)
        # ───────────────────────────────────────────────────────
        
        report_count = 0
        
        for i, cell in enumerate(cells[:30]):
            # Get cell leader
            cell_leader = None
            for user in session.identity_map.values():
                if isinstance(user, User) and user.cell_id == cell.id:
                    cell_leader = user
                    break
            
            if cell_leader is None:
                continue
            
            # Create report
            meeting_date = date.today() - timedelta(days=date.today().weekday() + 1)
            week_start = meeting_date - timedelta(days=meeting_date.weekday())
            week_end = week_start + timedelta(days=6)
            submission_deadline = datetime.combine(week_end, datetime.min.time()).replace(hour=9)
            
            report = CellReport(
                cell_id=cell.id,
                submitted_by_id=cell_leader.id,
                meeting_date=meeting_date,
                week_start_date=week_start,
                week_end_date=week_end,
                actual_meeting_day="sunday",
                submission_deadline=submission_deadline,
                status="submitted",
                submitted_at=datetime.utcnow(),
                meeting_type="Bible Study",
                meeting_duration=90,
                total_attendance=20 + (i % 30),
                first_timers=i % 5,
                number_saved=i % 3,
                filled_holy_ghost=i % 2,
                new_members=i % 2,
                souls_retained=i % 4,
                souls_won=i % 3,
                souls_on_tracker=5 + (i % 10),
                finance_oblation=5000,
                finance_offerings=3000,
                finance_tithes=8000,
                finance_thanksgiving=2000,
                finance_seed=1000,
                finance_partnership=0,
                finance_first_fruits=0,
                finance_total=19000,
                testimonies=f"Amazing week with {i % 3} souls won!",
                challenges="None major",
                pastors_remarks="Excellent work"
            )
            session.add(report)
            report_count += 1
        
        await session.flush()
        await session.commit()
        
        print(f"✅ {report_count} Sample reports created\n")
        
        print("=" * 60)
        print("🎉 DATABASE SEEDING COMPLETE!")
        print("=" * 60)
        print("\n📊 SUMMARY:")
        print(f"  Zones:                1")
        print(f"  Fellowships:          {len(fellowships)}")
        print(f"  Senior Cells:         {len(senior_cells)}")
        print(f"  Cells:                {len(cells)}")
        print(f"  Total Users:          {1 + 1 + len(fellowships) + len(senior_cells) + len(cells)}")
        print(f"  Sample Reports:       {report_count}")
        
        print("\n📱 TEST CREDENTIALS:")
        print(f"  System Admin:         +237690000000 / 123456")
        print(f"  Zonal Admin:          +237690100001 / 123456")
        print(f"  Fellowship Pastor:    +237690200000 / 123456")
        print(f"  Senior Cell Leader:   +237690300001 / 123456")
        print(f"  Cell Leader:          +237690400001 / 123456")
        
        print("\n🔗 Test Login: http://localhost:8000/docs")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())










# """
# Seed Script for BLW Cell Track Database
# Populates Zone B (Cameroon) with realistic test data
# Run once: python seed_database.py
# """

# import asyncio
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from datetime import datetime, date, timedelta
# from uuid import uuid4
# import os
# from dotenv import load_dotenv

# # Import your models
# from database import ASYNC_DATABASE_URL
# from models import (
#     Base, Zone, Fellowship, SeniorCell, Cell, User, CellReport
# )
# from auth import hash_pin

# load_dotenv()

# # Setup async session
# engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
# AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# async def seed_database():
#     """Populate database with test data"""
    
#     async with engine.begin() as conn:
#         # Drop and recreate all tables
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)
    
#     async with AsyncSessionLocal() as session:
#         print("🌱 Seeding Zone B (Cameroon)...")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE ZONE B
#         # ═══════════════════════════════════════════════════════════
        
#         zone_b = Zone(
#             name="Cameroon Zone B",
#             location="Cameroon (Bamenda, Yaounde, Dschang, CAR, Eq. Guinea, Sao Tome)",
#             description="BLW Cameroon Zone B : East & Central Africa Region"
#         )
#         session.add(zone_b)
#         await session.flush()
#         zone_b_id = zone_b.id
#         print(f"✅ Zone B created: {zone_b_id}")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE SYSTEM ADMIN
#         # ═══════════════════════════════════════════════════════════
        
#         system_admin = User(
#             phone="+2376981364856",
#             name="System Admin",
#             pin_hash=hash_pin("123456"),
#             role="system_admin",
#             is_active=True
#         )
#         session.add(system_admin)
#         await session.flush()
#         print(f"✅ System Admin created: +237690000000 / 123456")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE ZONAL ADMIN
#         # ═══════════════════════════════════════════════════════════
        
#         zonal_admin = User(
#             phone="+237690100001",
#             name="Zonal Secretary : BLW Cameroon Zone B",
#             pin_hash=hash_pin("123456"),
#             role="zonal_admin",
#             zone_id=zone_b_id,
#             is_active=True
#         )
#         session.add(zonal_admin)
#         await session.flush()
#         print(f"✅ Zonal Admin created: +237690100001 / 123456")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE FELLOWSHIPS (9 total)
#         # ═══════════════════════════════════════════════════════════
        
#         fellowships_data = [
#             ("BLW University Of Bamenda", "Bambili, North West Region"),
#             ("BLW National Polytechnic Yaounde", "Yaounde, Center Region"),
#             ("BLW Siantou", "Yaounde, Center Region"),
#             ("BLW University Of Dschang", "Dschang, West Region"),
#             ("BLW National Polytechnic Bamenda", "Bamenda, North West Region"),
#             ("CAR Mission", "Bangui, Central African Republic"),
#             ("Equatorial Guinea", "Malabo, Equatorial Guinea"),
#             ("Sao Tome Fellowship", "Sao Tome, Sao Tome & Principe"),
#             ("Libreville Extension", "Libreville, Gabon"),
#         ]
        
#         fellowships = []
#         for i, (name, location) in enumerate(fellowships_data):
#             fellowship = Fellowship(
#                 name=name,
#                 location=location,
#                 zone_id=zone_b_id
#             )
#             session.add(fellowship)
#             await session.flush()
#             fellowships.append(fellowship)
#             print(f"  ✅ Fellowship {i+1}: {name}")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE FELLOWSHIP PASTORS (1 per fellowship)
#         # ═══════════════════════════════════════════════════════════
        
#         pastor_names = [
#             "Pastor Stanley N",
#             "Pastor Nelson Yembe",
#             "Pastor David Siantou",
#             "Pastor Grace Dschang",
#             "Pastor Njini Rabiatu",
#             "Pastor Che Titus",
#             "Pastor Emmanuel Kevin",
#             "Pastor Rebecca Sao Tome",
#             "Pastor Michael Congo",
#         ]
        
#         for i, (fellowship, pastor_name) in enumerate(zip(fellowships, pastor_names)):
#             pastor = User(
#                 phone=f"+237690200{i:03d}",
#                 name=pastor_name,
#                 pin_hash=hash_pin("123456"),
#                 role="fellowship_pastor",
#                 fellowship_id=fellowship.id,
#                 zone_id=zone_b_id,
#                 is_active=True
#             )
#             session.add(pastor)
#             print(f"  ✅ Pastor: {pastor_name}")
        
#         await session.flush()
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE SENIOR CELLS (2 per fellowship = 18 total, use 12 for MVP)
#         # ═══════════════════════════════════════════════════════════
        
#         senior_cells = []
#         senior_cl_count = 0
        
#         for fellowship in fellowships[:6]:  # First 6 fellowships (12 senior cells)
#             for j in range(2):
#                 division = chr(65 + j)  # A, B
#                 senior_cell = SeniorCell(
#                     name=f"{fellowship.name} - Division {division}",
#                     fellowship_id=fellowship.id
#                 )
#                 session.add(senior_cell)
#                 await session.flush()
#                 senior_cells.append(senior_cell)
                
#                 # Create senior cell leader
#                 senior_cl_count += 1
#                 senior_cl = User(
#                     phone=f"+237690300{senior_cl_count:03d}",
#                     name=f"Elder {chr(64 + senior_cl_count)} - {senior_cell.name}",
#                     pin_hash=hash_pin("123456"),
#                     role="senior_cell_leader",
#                     senior_cell_id=senior_cell.id,
#                     fellowship_id=fellowship.id,
#                     zone_id=zone_b_id,
#                     is_active=True
#                 )
#                 session.add(senior_cl)
#                 print(f"  ✅ Senior Cell: {senior_cell.name}")
        
#         await session.flush()
#         print(f"✅ {len(senior_cells)} Senior Cells + {senior_cl_count} Leaders created")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE CELLS (6 per senior cell = 72 total)
#         # ═══════════════════════════════════════════════════════════
        
#         cells = []
#         cell_leader_count = 0
        
#         for senior_cell in senior_cells:
#             for cell_num in range(1, 7):  # 6 cells per senior cell
#                 cell = Cell(
#                     name=f"{senior_cell.name} - Cell {cell_num}",
#                     senior_cell_id=senior_cell.id,
#                     default_meeting_day=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][cell_num - 1],
#                     meeting_time=None  # Set later if needed
#                 )
#                 session.add(cell)
#                 await session.flush()
#                 cells.append(cell)
                
#                 # Create cell leader
#                 cell_leader_count += 1
#                 cell_leader = User(
#                     phone=f"+237690400{cell_leader_count:03d}",
#                     name=f"Brother/Sister {cell_leader_count} - {cell.name}",
#                     pin_hash=hash_pin("123456"),
#                     role="cell_leader",
#                     cell_id=cell.id,
#                     senior_cell_id=senior_cell.id,
#                     fellowship_id=senior_cell.fellowship_id,
#                     zone_id=zone_b_id,
#                     is_active=True
#                 )
#                 session.add(cell_leader)
        
#         await session.flush()
#         print(f"✅ {len(cells)} Cells + {cell_leader_count} Cell Leaders created")
        
#         # ═══════════════════════════════════════════════════════════
#         # CREATE SAMPLE REPORTS (Submit reports for some cells)
#         # ═══════════════════════════════════════════════════════════
        
#         # Submit reports for first 30 cells
#         report_count = 0
        
#         for i, cell in enumerate(cells[:30]):
#             # Get cell leader
#             result = await session.execute(
#                 __import__('sqlalchemy').select(User).where(User.cell_id == cell.id)
#             )
#             cell_leader = result.scalar_one()
            
#             # Create report for last Sunday
#             meeting_date = date.today() - timedelta(days=date.today().weekday() + 1)
#             week_start = meeting_date - timedelta(days=meeting_date.weekday())
#             week_end = week_start + timedelta(days=6)
#             submission_deadline = datetime.combine(week_end, __import__('datetime').time(9, 0, 0))
            
#             report = CellReport(
#                 cell_id=cell.id,
#                 submitted_by_id=cell_leader.id,
#                 meeting_date=meeting_date,
#                 week_start_date=week_start,
#                 week_end_date=week_end,
#                 actual_meeting_day="sunday",
#                 submission_deadline=submission_deadline,
#                 status="submitted",
#                 submitted_at=datetime.utcnow(),
#                 meeting_type="Bible Study",
#                 meeting_duration=90,
#                 total_attendance=20 + (i % 30),
#                 first_timers=i % 5,
#                 number_saved=i % 3,
#                 filled_holy_ghost=i % 2,
#                 new_members=i % 2,
#                 souls_retained=i % 4,
#                 souls_won=i % 3,
#                 souls_on_tracker=5 + (i % 10),
#                 finance_oblation=5000,
#                 finance_offerings=3000,
#                 finance_tithes=8000,
#                 finance_thanksgiving=2000,
#                 finance_seed=1000,
#                 finance_partnership=0,
#                 finance_first_fruits=0,
#                 finance_total=19000,
#                 testimonies=f"Cell {i} witnessed {i % 3} souls won this week!",
#                 challenges="None major",
#                 pastors_remarks="Good work team"
#             )
#             session.add(report)
#             report_count += 1
        
#         await session.flush()
#         print(f"✅ {report_count} Sample reports created")
        
#         # ═══════════════════════════════════════════════════════════
#         # COMMIT ALL
#         # ═══════════════════════════════════════════════════════════
        
#         await session.commit()
        
#         print("\n" + "="*60)
#         print("🎉 DATABASE SEEDING COMPLETE!")
#         print("="*60)
#         print("\n📊 SUMMARY:")
#         print(f"  Zones:           1 (Zone B)")
#         print(f"  Fellowships:     {len(fellowships)}")
#         print(f"  Senior Cells:    {len(senior_cells)}")
#         print(f"  Cells:           {len(cells)}")
#         print(f"  Users:           {1 + 1 + len(fellowships) + len(senior_cells) + len(cells)} total")
#         print(f"    - System Admin:        1")
#         print(f"    - Zonal Admins:        1")
#         print(f"    - Fellowship Pastors:  {len(fellowships)}")
#         print(f"    - Senior Cell Leaders: {len(senior_cells)}")
#         print(f"    - Cell Leaders:        {len(cells)}")
#         print(f"  Reports:         {report_count} sample")
        
#         print("\n📱 TEST CREDENTIALS:")
#         print(f"  System Admin:    +237690000000 / 123456")
#         print(f"  Zonal Admin:     +237690100001 / 123456")
#         print(f"  Fellowship Pastor: +237690200000 / 123456 (any pastor)")
#         print(f"  Senior Cell Leader: +237690300001 / 123456 (any senior CL)")
#         print(f"  Cell Leader:     +237690400001 / 123456 (any cell leader)")
        
#         print("\n🔗 Ready to test at: http://localhost:8000/docs")


# if __name__ == "__main__":
#     asyncio.run(seed_database())