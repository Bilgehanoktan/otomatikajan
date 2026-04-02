import asyncio
import unittest
import time
from unittest.mock import AsyncMock, patch, MagicMock

from core.agi.operational.kinetic_arbiter import kinetic_arbiter, ArbiterRequest
from core.agi.consciousness.affective_core import affective_core

class TestKineticArbitrationV43(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        # Start arbiter
        await kinetic_arbiter.start()
        # Reset slots
        kinetic_arbiter._active_slots = 0
        kinetic_arbiter._max_total_slots = 2 # Small for testing

    async def asyncTearDown(self):
        await kinetic_arbiter.stop()

    async def test_priority_queue_logic(self):
        print("\n--- Phase 43: Kinetic Arbitration Verification ---")
        
        # 1. Fill slots
        await kinetic_arbiter.acquire_slot("tech_writer", "t1")
        await kinetic_arbiter.acquire_slot("tech_writer", "t2")
        print("Slots filled with low-prio tasks.")
        
        # 2. Queue two tasks: Low prio then High prio
        # Note: We simulate the order of arrival
        t_low_prio = asyncio.create_task(kinetic_arbiter.acquire_slot("tech_writer", "t3"))
        await asyncio.sleep(0.05)
        t_high_prio = asyncio.create_task(kinetic_arbiter.acquire_slot("self_governor", "t4"))
        
        print("Tasks queued. Releasing a slot...")
        
        # 3. Release one slot. The High prio task should jump ahead in the priority queue.
        # Wait a bit to ensure they are in the queue
        await asyncio.sleep(0.1)
        kinetic_arbiter.release_slot()
        
        # Wait for one of them to finish
        done, pending = await asyncio.wait([t_low_prio, t_high_prio], return_when=asyncio.FIRST_COMPLETED)
        
        # Check which one finished first
        finished_task = list(done)[0]
        if finished_task == t_high_prio:
            print("Priority Bypass: SUCCESS (Self Governor jumped Tech Writer)")
            self.assertTrue(True)
        else:
            print("Priority Bypass: FAILED (Tech Writer finished first)")
            self.fail("Low priority task finished before high priority task in a congested queue.")

    async def test_affective_pacing(self):
        # Set high stress to increase pacing
        affective_core.state["internal_stress"] = 0.9
        pacing = kinetic_arbiter._calculate_pacing()
        print(f"Pacing under high stress: {pacing:.2f}s")
        self.assertGreater(pacing, 0.5)
        
        # Set low stress/high energy
        affective_core.state["internal_stress"] = 0.1
        affective_core.state["energy_reserve"] = 1.0
        pacing = kinetic_arbiter._calculate_pacing()
        print(f"Pacing under low stress: {pacing:.2f}s")
        self.assertEqual(pacing, 0.1)

if __name__ == "__main__":
    unittest.main()
