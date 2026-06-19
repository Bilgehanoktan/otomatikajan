-- migration_phase30.sql
-- Sovereign AGI Phase 30: Institutional Compliance & Proof Fabric

-- [DECISION LINEAGE]
-- Bu tablo otonom kararların mühürlendiği yerdir.
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='decision_lineage' AND column_name='integrity_hash') THEN
        ALTER TABLE decision_lineage ADD COLUMN integrity_hash VARCHAR(64);
        CREATE INDEX ix_decision_lineage_integrity_hash ON decision_lineage (integrity_hash);
        RAISE NOTICE 'Added integrity_hash to decision_lineage';
    END IF;
END $$;

-- Geçmiş kayıtları mühürle (id bazlı basit başlangıç)
UPDATE decision_lineage 
SET integrity_hash = md5(id::text || 'CONSTITUTION_V30') 
WHERE integrity_hash IS NULL;

-- [LLM COST LOGS]
-- Bütçe verimliliği için model router loglarına indeks ekle
CREATE INDEX IF NOT EXISTS ix_llm_cost_logs_created_at_cost ON llm_cost_logs (created_at, cost_usd);

-- [POLICY PROPOSALS]
-- Tekliflerin Git mühürleme durumu için indeks
CREATE INDEX IF NOT EXISTS ix_policy_proposals_git_sha ON policy_proposals (git_commit_sha);
