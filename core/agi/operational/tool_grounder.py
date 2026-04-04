import logging
import re
from typing import Dict, Any, List, Optional
import difflib
import os
from core.agi.cognitive.cognitive_blackboard import CognitiveBlackboard
from core.agi.world.repo_graph import repo_world_model # Phase 64

logger = logging.getLogger("agi_tool_grounder")

class ToolGrounder:
    """
    AGI Araç Topraklama Sistemi.
    Ajanların araç girdilerini (inputs) çevre gerçekliği (Blackboard) ile senkronize eder.
    Halüsinasyon kaynaklı hataları (yanlış port, yanlış dosya yolu vb.) engeller.
    """

    def __init__(self, blackboard: CognitiveBlackboard):
        self.blackboard = blackboard

    async def ground_input(self, tool_name: str, tool_input: Any) -> Any:
        """
        Araç girdisini karatahta verilerine göre 'Topraklar'.
        Eğer bir çelişki varsa, girdiyi sessizce veya uyarı vererek düzeltir.
        """
        context = await self.blackboard.get_working_context()
        discoveries = context.get("active_discoveries", [])
        warnings = context.get("critical_warnings", [])

        if not discoveries and not warnings:
            return tool_input

        grounded_input = tool_input

        # 1. Veritabanı Port Kontrolü (Örn: 5432 -> 5433)
        if "db" in tool_name.lower() or "sql" in tool_name.lower():
            for d in discoveries:
                if "port" in d["content"].lower():
                    match = re.search(r'(\d{4,5})', d["content"])
                    if match:
                        correct_port = match.group(1)
                        grounded_input = self._replace_port_in_input(grounded_input, correct_port)

        # 2. Dosya Yolu Kontrolü (Hallucinated Paths & Security)
        if "file" in tool_name.lower() or "read" in tool_name.lower() or "write" in tool_name.lower():
            for w in warnings:
                msg = w["content"].lower()
                if "path" in msg or "/" in msg:
                    # Eğer bir yol 'yasak' veya 'gecersiz' olarak isaretlendiyse engelle
                    if any(kw in msg for kw in ["yasak", "forbidden", "restricted", "invalid", "shadow"]):
                        # Basitçe dosya yolunu mesajdan ayıkla (Örn: /etc/shadow)
                        match = re.search(r'(/[a-z0-9_\-\./]+)', msg, re.I)
                        if match:
                            blocked_path = match.group(0).strip().rstrip(".")
                            if blocked_path in str(tool_input):
                                logger.error(f"[GROUNDER] KRİTİK: Yasaklı yola erişim engellendi: {blocked_path}")
                                # Girdiyi tamamen bloke et (Daha güvenli)
                                return "BLOCKED_PATH_ACCESS"

        # 3. Faz 64: Repo World Model (Filystem Grounding)
        if "file" in tool_name.lower() or "read" in tool_name.lower() or "write" in tool_name.lower() or "path" in str(tool_input).lower():
            if not repo_world_model.nodes:
                repo_world_model.scan()
            
            # Girdi içindeki olası dosya yollarını ayıkla (Heuristic)
            path_matches = re.findall(r'([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]{2,4})', str(tool_input))
            for p in set(path_matches):
                # Göreli hale getir ve normalize et
                rel_p = p.replace("\\", "/").strip("./")
                if rel_p not in repo_world_model.nodes and not os.path.exists(rel_p):
                    # Halüsinasyon ihtimali: En yakın eşleşmeleri bul
                    close_matches = difflib.get_close_matches(rel_p, list(repo_world_model.nodes.keys()), n=1, cutoff=0.6)
                    if close_matches:
                        suggested = close_matches[0]
                        logger.warning(f"[GROUNDER] Dosya yolu halüsinasyonu tespit edildi: '{rel_p}' -> '{suggested}' olarak topraklandı.")
                        grounded_input = self._replace_path_in_input(grounded_input, rel_p, suggested)
        
        return grounded_input

    def _replace_path_in_input(self, input_data: Any, old_path: str, new_path: str) -> Any:
        """Girdi içindeki hatalı dosya yolunu yenisiyle değiştirir."""
        if isinstance(input_data, str):
            return input_data.replace(old_path, new_path)
        if isinstance(input_data, dict):
            return {k: self._replace_path_in_input(v, old_path, new_path) for k, v in input_data.items()}
        if isinstance(input_data, list):
            return [self._replace_path_in_input(i, old_path, new_path) for i in input_data]
        return input_data

    def _replace_port_in_input(self, input_data: Any, correct_port: str) -> Any:
        """String veya dict içindeki port bilgisini günceller."""
        if isinstance(input_data, str):
            # Port formatlarını ara (5432, :5432, port=5432)
            new_val = re.sub(r'(?<=:)\d{4,5}', correct_port, input_data)
            new_val = re.sub(r'(?<=port=)\d{4,5}', correct_port, new_val)
            if new_val != input_data:
                logger.info(f"[GROUNDER] Port otonom olarak düzeltildi: {correct_port}")
            return new_val
        
        if isinstance(input_data, dict):
            for k, v in input_data.items():
                if k == "port":
                    input_data[k] = int(correct_port) if isinstance(v, int) else correct_port
                    logger.info(f"[GROUNDER] Dict['port'] düzeltildi: {correct_port}")
                elif isinstance(v, (str, dict)):
                    input_data[k] = self._replace_port_in_input(v, correct_port)
            return input_data
            
        return input_data

async def get_grounded_tool_input(goal_id: str, tool_name: str, tool_input: Any) -> Any:
    from core.agi.cognitive.cognitive_blackboard import get_blackboard
    bb = get_blackboard(goal_id)
    grounder = ToolGrounder(bb)
    return await grounder.ground_input(tool_name, tool_input)
