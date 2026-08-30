import asyncio, sys, os

sys.path.insert(0, "d:/01 R/Research Antigravity/01 R/packages/shared")
os.environ["NEON_DATABASE_URL"] = (
    "postgresql://neondb_owner:npg_xu2LWXchSb7U"
    "@ep-dark-mode-az3pl4xm-pooler.c-3.ap-southeast-1.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)

async def test():
    from shared.db import get_pool, upsert_job, persist_stage_run, persist_artifact, get_stage_results

    pool = await get_pool()
    print("Pool acquired from Neon")

    # Test job upsert
    test_job_id = "00000000-0000-0000-0000-000000000001"
    await upsert_job(
        job_id=test_job_id,
        project_name="Test Project",
        status="running",
        current_stage="requirements",
    )
    print("Job row upserted")

    # Test stage_run insert
    row_id = await persist_stage_run(
        job_id=test_job_id,
        stage="requirements",
        status="complete",
        payload={"functional_requirements": [{"id": "FR-1", "title": "Test"}]},
        duration_ms=1234,
    )
    print(f"Stage run row inserted: {row_id}")

    # Test artifact insert
    art_id = await persist_artifact(
        job_id=test_job_id,
        stage="hld",
        kind="architecture_diagram",
        filename="arch.mmd",
        uri="D:/AgentOutputs/hld/00000000-0000-0000-0000-000000000001/arch.mmd",
        mime_type="text/plain",
        size_bytes=1024,
    )
    print(f"Artifact row inserted: {art_id}")

    # Read back
    rows = await get_stage_results(test_job_id)
    print(f"Stage results fetched: {len(rows)} rows")

    # Cleanup test rows
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM jobs WHERE id = $1::uuid", test_job_id)
    print("Test rows cleaned up")

    print("\nALL SHARED DB TESTS PASSED")
    await pool.close()

asyncio.run(test())
