"""
HTML & Playwright Ultra HD Slide Renderer for @Ai_gucum_.
Renders pixel-perfect 1080x1920 modern web carousel slides with Tailwind-style CSS, Google Fonts, and Glassmorphism.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = BASE_DIR / "workspace" / "carousel_engine" / "slide_template.html"
BRAND_HANDLE = "@Ai_gucum_"

def build_slide_html(slide_data: Dict[str, Any], total_slides: int = 6) -> str:
    """Compiles a slide data dictionary into full HTML5 using slide_template.html."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    slide_num = slide_data.get("slide_number", 1)
    progress_percent = int((slide_num / total_slides) * 100)
    
    badge_icon = slide_data.get("badge_icon", "⚡")
    badge_text = slide_data.get("badge", "YAPAY ZEKA TRICK")
    
    # Title & Subtitle
    title_raw = slide_data.get("title", "")
    # Add highlight span to last word or specific target
    words = title_raw.split(" ")
    if len(words) > 3:
        highlight_part = " ".join(words[-2:])
        base_part = " ".join(words[:-2])
        title_html = f'{base_part} <span class="highlight">{highlight_part}</span>'
    else:
        title_html = f'<span class="highlight">{title_raw}</span>'
        
    subtitle_raw = slide_data.get("subtitle", "")
    subtitle_html = f'<p class="subtitle-text">{subtitle_raw}</p>' if subtitle_raw else ""

    # Dynamic Body Content
    body_html = ""

    # 1. Code Snippet Block (Slide 3)
    if "code_snippet" in slide_data:
        code_data = slide_data["code_snippet"]
        lang = code_data.get("lang", "PYTHON")
        code_str = code_data.get("code", "")
        
        body_html += f'''
        <div class="code-container">
          <div class="code-header">
            <div class="code-dots">
              <div class="code-dot dot-red"></div>
              <div class="code-dot dot-yellow"></div>
              <div class="code-dot dot-green"></div>
            </div>
            <div class="code-lang"><code>{lang}</code></div>
          </div>
          <div class="code-content">{code_str}</div>
        </div>
        '''

    # 2. Hero Summary List (Slide 1)
    if "hero_highlights" in slide_data:
        items = slide_data["hero_highlights"]
        body_html += '<div class="hero-summary-card">'
        for item in items:
            body_html += f'''
            <div class="summary-item">
              <div class="summary-icon">{item.get('icon', '⚡')}</div>
              <div>{item.get('text', '')}</div>
            </div>
            '''
        body_html += '</div>'

    # 3. Comparison Matrix (Slide 2)
    if "comparison_matrix" in slide_data:
        matrix = slide_data["comparison_matrix"]
        body_html += '<div class="comparison-grid">'
        for box in matrix:
            is_hl = "highlight" if box.get("is_highlight") else ""
            body_html += f'''
            <div class="comp-box {is_hl}">
              <div class="comp-title">{box.get('title', '')}</div>
              <div class="comp-value">{box.get('value', '')}</div>
            </div>
            '''
        body_html += '</div>'

    # 4. Feature Cards (Slide 4/5)
    if "features" in slide_data:
        for feat in slide_data["features"]:
            body_html += f'''
            <div class="feature-card">
              <div class="feature-card-header">
                <span>{feat.get('icon', '🚀')}</span> {feat.get('title', '')}
              </div>
              <div class="feature-card-desc">{feat.get('desc', '')}</div>
            </div>
            '''

    # 5. CTA Box (Slide 6)
    if "cta_box" in slide_data:
        cta = slide_data["cta_box"]
        body_html += f'''
        <div class="cta-container">
          <div class="cta-badge">{cta.get('badge', 'YORUM YAP & REHBERİ AL')}</div>
          <div class="cta-text">"{cta.get('trigger_word', 'DEEPSEEK')}" YAZ</div>
          <div class="cta-sub">{cta.get('subtext', 'Tüm bağlantı ve gizli rehberi anında DM olarak göndereyim!')}</div>
        </div>
        '''

    footer_hint = slide_data.get("footer", "Kaydırın > Detaylar İçeride")

    # Replace placeholders
    html_out = template.replace("{{PROGRESS_PERCENT}}", str(progress_percent))
    html_out = html_out.replace("{{BADGE_ICON}}", badge_icon)
    html_out = html_out.replace("{{BADGE_TEXT}}", badge_text)
    html_out = html_out.replace("{{SLIDE_NUM}}", str(slide_num))
    html_out = html_out.replace("{{TOTAL_SLIDES}}", str(total_slides))
    html_out = html_out.replace("{{TITLE_HTML}}", title_html)
    html_out = html_out.replace("{{SUBTITLE_HTML}}", subtitle_html)
    html_out = html_out.replace("{{BODY_HTML}}", body_html)
    html_out = html_out.replace("{{BRAND_HANDLE}}", BRAND_HANDLE)
    html_out = html_out.replace("{{FOOTER_HINT}}", footer_hint)

    return html_out

def render_slide_with_playwright(slide_data: Dict[str, Any], output_path: Path, total_slides: int = 6) -> str:
    """Launches Playwright headless browser, loads HTML slide, and saves 1080x1920 PNG screenshot."""
    full_html = build_slide_html(slide_data, total_slides=total_slides)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page = context.new_page()

        page.set_content(full_html, wait_until="networkidle")
        # Give Google Fonts a split second to render perfectly
        time.sleep(0.5)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output_path), full_page=True, type="png")
        browser.close()

    return str(output_path)
