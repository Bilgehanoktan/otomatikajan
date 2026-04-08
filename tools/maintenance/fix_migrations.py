import os
import re

versions_dir = r"e:/ai_company_faz12.1/packages/persistence/migrations/alembic/versions"

pattern = re.compile(r"postgresql\.JSONB(\(astext_type=sa\.Text\(\)\))?")

# sa'nın import edildiğinden emin ol (zaten çoğu dosyada var)
# postgresql migration'larda genelde 'from sqlalchemy.dialects import postgresql' var

for filename in os.listdir(versions_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(versions_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # JSONB -> sa.JSON()
        # with_variant ekleyerek cross-db yapalım
        new_content = content.replace("postgresql.JSONB", "sa.JSON")
        
        # '::jsonb' gibi postgres specific server default'ları temizle (SQLite için)
        new_content = new_content.replace("::jsonb", "")
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filename}")
