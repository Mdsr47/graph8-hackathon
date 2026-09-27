import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db

def test_auth_seeding_and_login():
    async def _test():
        # 1. Initialize DB and seed
        await db.init_db()

        # 2. Verify demo user exists
        user = await db.get_user_by_email("demo@graph8.ai")
        assert user is not None
        assert user["email"] == "demo@graph8.ai"
        assert user["role"] == "Lead RevOps"

        # 3. Verify valid credentials
        verified = await db.verify_user_credentials("demo@graph8.ai", "password123")
        assert verified is not None
        assert verified["email"] == "demo@graph8.ai"

        # 4. Verify invalid credentials
        invalid = await db.verify_user_credentials("demo@graph8.ai", "wrongpassword")
        assert invalid is None

        # 5. Verify case insensitivity
        upper_verified = await db.verify_user_credentials("DEMO@GRAPH8.AI", "password123")
        assert upper_verified is not None
    
    asyncio.run(_test())
