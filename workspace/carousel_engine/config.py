import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "artifacts" / "carousels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Image Specs (1080x1920 Ultra HD 9:16 Aspect Ratio)
WIDTH = 1080
HEIGHT = 1920

# Premium Design System - Cyber Tech Glassmorphic Theme
COLORS = {
    "bg_start": (7, 10, 17),          # Deep Obsidian
    "bg_end": (15, 23, 42),          # Cyber Navy
    "card_bg": (18, 24, 38, 235),     # Translucent Cyber Glass
    "card_border": (56, 189, 248, 80),# Cyan Glow Border
    "primary_text": (255, 255, 255),  # Pure Crisp White
    "secondary_text": (148, 163, 184),# Soft Silver
    "muted_text": (100, 116, 139),    # Slate Muted
    "accent_blue": (59, 130, 246),    # Electric Blue
    "accent_purple": (168, 85, 247),  # Neon Purple
    "accent_cyan": (0, 240, 255),     # Cyber Cyan
    "accent_green": (16, 185, 129),   # Vibrant Emerald
    "accent_warning": (245, 158, 11), # Amber Gold
    "accent_danger": (255, 51, 102),  # Crimson Red
}

# Brand Config
BRAND_HANDLE = "@Ai_gucum_"
BRAND_NAME = "AI Gücüm"

# Hashtags for AI & Software Tools Niche
DEFAULT_HASHTAGS = [
    "#aigucum", "#yapayzeka", "#yazılım", "#python", "#kodlama", "#ai", 
    "#cursorai", "#yazılımcı", "#teknoloji", "#yazılımtrendleri", 
    "#otomasyon", "#verimlilik", "#affiliatemarketing"
]
