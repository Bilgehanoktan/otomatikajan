"""
Sovereign AGI — Phase 27
scripts/run_regional_mesh_node.py
Activates the real distributed backend for a specific region.
"""
import asyncio
import os
import signal
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.consensus_engine import get_consensus_engine
from libs.mesh.event_bridge import event_bridge
from libs.mesh.state_fabric import state_fabric
from services.observability.logging import get_logger

logger = get_logger("mesh.runner")

async def handle_global_event(event: dict):
    """Callback for EventBridge: Processes updates from other regions."""
    e_type = event.get("type")
    payload = event.get("payload", {})
    
    if e_type == "mesh:state:updates":
        # Other region pulsed. Log visibility
        logger.debug(f"Mesh Update received from {payload.get('region')}")
    elif e_type == "failover_command":
        logger.warning(f"CRITICAL: Remote failover command received: {payload}")

async def run_node(region_id: str):
    logger.info(f"--- ACTIVATING SOVEREIGN MESH NODE: {region_id} (R-03) ---")
    
    # 1. Start Consensus Engine (HA Role Arbitration)
    consensus = get_consensus_engine(region_id)
    asyncio.create_task(consensus.start_consensus_loop())
    
    # 2. Start Event Bridge (Cross-Region Broadcast)
    asyncio.create_task(event_bridge.start_listening(handle_global_event))
    
    # 3. Main Sync Loop
    while True:
        try:
            # Sync Fleet State to Global Fabric
            await fleet_manager.sync_mesh_state(region_id)
            
            # Broadcast our presence once per minute as a durable event
            await event_bridge.broadcast_event("region_heartbeat", {
                "region": region_id,
                "role": consensus.current_role
            })
            
            # Update Dashboard/Ops state
            logger.info(f"[{region_id}] Role: {consensus.current_role.upper()} | Syncing state to Global Fabric...")
            
        except Exception as e:
            logger.error(f"Sync loop error: {e}")
            
        await asyncio.sleep(10)

if __name__ == "__main__":
    region = os.getenv("REGION_ID", "us-east-1")
    try:
        asyncio.run(run_node(region))
    except KeyboardInterrupt:
        logger.info("Mesh node shutting down...")
