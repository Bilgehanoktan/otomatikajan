import os

directories = [
    "apps/api/routers",
    "apps/api/support",
    "apps/worker/tasks",
    "apps/worker/runtime",
    "apps/dashboard/js",
    "apps/dashboard/css",
    "packages/contracts/dto",
    "packages/persistence/models",
    "packages/persistence/repositories",
    "packages/persistence/migrations/alembic",
    "packages/llm_gateway/cost",
    "packages/repair_engine/application",
    "packages/orchestration/application",
    "packages/orchestration/domain",
    "packages/orchestration/ceo",
    "packages/orchestration/cognitive_runtime",
    "packages/orchestration/experimental",
    "packages/orchestration/legacy",
    "packages/integrations/deerflow",
    "packages/integrations/telegram",
    "packages/integrations/webhooks",
    "packages/healing",
    "packages/memory",
    "packages/skills",
    "docs/test_reports",
    "runtime/data",
    "runtime/logs",
    "runtime/tmp",
    "runtime/uploads",
    "tools/debug",
    "tools/verify",
    "tools/maintenance",
    "tools/migration",
    "external/vendor",
    "external/agent_assets",
    "external/everything_claude_code"
]

for d in directories:
    dir_path = os.path.join("e:/ai_company_faz12.1", d)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created: {dir_path}")
    else:
        print(f"Exists: {dir_path}")
