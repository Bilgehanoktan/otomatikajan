"""
Ultra-Premium Image Creator Module using PIL (Pillow).
Renders 1080x1920 Ultra HD 9:16 Cyber-Tech Glassmorphic Social Media Carousel Slides.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from workspace.carousel_engine.config import WIDTH, HEIGHT, COLORS, OUTPUT_DIR, BRAND_HANDLE, BRAND_NAME

def clean_text(text: str) -> str:
    """Strictly cleans non-printable unicode / emoji variation selectors that cause box artifacts."""
    if not text:
        return ""
    allowed = set("abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ0123456789 .,!?:;-_/()[]{}><=@+*%&'\"")
    cleaned = "".join(c for c in text if c in allowed or (ord(c) >= 32 and ord(c) <= 126))
    return " ".join(cleaned.split()).strip()

def create_radial_gradient_background(width: int, height: int) -> Image.Image:
    """Creates a deep dark background with glowing ambient light orbs."""
    img = Image.new("RGBA", (width, height), (7, 10, 17, 255))
    
    # Glow orb 1 (Cyan top left)
    glow1 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw1 = ImageDraw.Draw(glow1)
    draw1.ellipse([ -150, -100, 650, 700 ], fill=(0, 240, 255, 40))
    glow1 = glow1.filter(ImageFilter.GaussianBlur(120))
    
    # Glow orb 2 (Purple bottom right)
    glow2 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(glow2)
    draw2.ellipse([ width - 650, height - 750, width + 150, height + 100 ], fill=(168, 85, 247, 35))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(140))
    
    # Glow orb 3 (Blue center accent)
    glow3 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw3 = ImageDraw.Draw(glow3)
    draw3.ellipse([ 200, 700, 880, 1380 ], fill=(59, 130, 246, 25))
    glow3 = glow3.filter(ImageFilter.GaussianBlur(160))

    img = Image.alpha_composite(img, glow1)
    img = Image.alpha_composite(img, glow2)
    img = Image.alpha_composite(img, glow3)
    return img

def get_font(size: int, is_bold: bool = False) -> ImageFont.ImageFont:
    """System font loader with fallback hierarchy."""
    font_names = [
        "segoeui.ttf", "segoeuib.ttf", "arial.ttf", "arialbd.ttf", 
        "calibri.ttf", "DejaVuSans.ttf"
    ]
    if is_bold:
        font_names.insert(0, "segoeuib.ttf")
        font_names.insert(1, "arialbd.ttf")

    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
            
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Wraps text lines cleanly to fit within max pixel width."""
    text = clean_text(text)
    words = text.split(" ")
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0] if bbox else len(test_line) * (font.size * 0.5)
        
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            
    if current_line:
        lines.append(current_line)
        
    return lines

def render_slide(slide_data: Dict[str, Any], total_slides: int = 6) -> str:
    """Renders an ultra-premium 1080x1920 slide image."""
    # 1. Base Ambient Background
    base_img = create_radial_gradient_background(WIDTH, HEIGHT)
    
    # 2. Main Glass Canvas Layer
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Card Geometry
    card_margin_x = 64
    card_margin_y = 100
    card_w = WIDTH - (card_margin_x * 2)
    card_h = HEIGHT - (card_margin_y * 2)
    card_box = (card_margin_x, card_margin_y, card_margin_x + card_w, card_margin_y + card_h)

    # Glass Card Background (Dark Glassmorphic Callout)
    draw.rounded_rectangle(card_box, radius=40, fill=(18, 24, 38, 230), outline=(56, 189, 248, 80), width=3)

    # 3. Top Progress Bar (1080px scale)
    progress_ratio = slide_data['slide_number'] / total_slides
    progress_w = int((card_w - 48) * progress_ratio)
    prog_y1 = card_margin_y + 24
    prog_y2 = card_margin_y + 32
    prog_x1 = card_margin_x + 24
    
    # Background track
    draw.rounded_rectangle((prog_x1, prog_y1, prog_x1 + card_w - 48, prog_y2), radius=4, fill=(40, 50, 75, 180))
    # Active track (Gradient cyan-blue glow)
    draw.rounded_rectangle((prog_x1, prog_y1, prog_x1 + progress_w, prog_y2), radius=4, fill=(0, 240, 255, 255))

    # 4. Fonts Initialization
    badge_font = get_font(24, is_bold=True)
    counter_font = get_font(24, is_bold=True)
    title_font = get_font(50, is_bold=True)
    subtitle_font = get_font(32, is_bold=False)
    body_font = get_font(28, is_bold=False)
    feature_title_font = get_font(32, is_bold=True)
    footer_font = get_font(24, is_bold=True)

    current_y = card_margin_y + 64
    content_x = card_margin_x + 48
    content_max_w = card_w - 96

    # 5. Header Row (Badge + Slide Counter)
    badge_text = clean_text(slide_data.get("badge", "YAPAY ZEKA")).upper()
    badge_color = COLORS["accent_cyan"] if slide_data["type"] in ["HOOK", "SOLUTION"] else (
        COLORS["accent_danger"] if slide_data["type"] in ["PROBLEM", "AGITATION"] else COLORS["accent_purple"]
    )
    
    # Badge Pill
    badge_bbox = badge_font.getbbox(badge_text)
    badge_w = (badge_bbox[2] - badge_bbox[0]) + 36 if badge_bbox else 220
    badge_h = 48
    draw.rounded_rectangle((content_x, current_y, content_x + badge_w, current_y + badge_h), radius=14, fill=badge_color)
    draw.text((content_x + 18, current_y + 10), badge_text, fill=(7, 10, 17), font=badge_font)

    # Counter Pill (SLAYT 1 / 6)
    counter_text = f"SLAYT {slide_data['slide_number']} / {total_slides}"
    counter_bbox = counter_font.getbbox(counter_text)
    counter_w = (counter_bbox[2] - counter_bbox[0]) if counter_bbox else 150
    counter_x = content_x + content_max_w - counter_w
    draw.text((counter_x, current_y + 10), counter_text, fill=COLORS["accent_cyan"], font=counter_font)

    current_y += badge_h + 44

    # 6. Hero Title Render
    if "title" in slide_data:
        title_lines = wrap_text(slide_data["title"], title_font, content_max_w)
        for line in title_lines:
            draw.text((content_x, current_y), line, fill=COLORS["primary_text"], font=title_font)
            current_y += 66
        current_y += 20

    # Accent Line Divider
    draw.line([(content_x, current_y), (content_x + 160, current_y)], fill=COLORS["accent_cyan"], width=6)
    current_y += 44

    # 7. Subtitle / Main Description Box
    if "subtitle" in slide_data and slide_data["subtitle"]:
        sub_lines = wrap_text(slide_data["subtitle"], subtitle_font, content_max_w)
        for line in sub_lines:
            draw.text((content_x, current_y), line, fill=COLORS["secondary_text"], font=subtitle_font)
            current_y += 46
        current_y += 32

    # 8. Slide 1 Highlights Box
    if "highlights" in slide_data:
        current_y += 24
        hl_box = (content_x, current_y, content_x + content_max_w, current_y + 240)
        draw.rounded_rectangle(hl_box, radius=24, fill=(30, 41, 59, 210), outline=(56, 189, 248, 90), width=2)
        
        hl_y = current_y + 28
        hl_font = get_font(30, is_bold=True)
        for item in slide_data["highlights"]:
            draw.text((content_x + 32, hl_y), clean_text(item), fill=COLORS["accent_cyan"], font=hl_font)
            hl_y += 62
            
        current_y += 280

    # 9. Slide 5 Features Block
    if "features" in slide_data:
        for feat in slide_data["features"]:
            feat_box = (content_x, current_y, content_x + content_max_w, current_y + 140)
            draw.rounded_rectangle(feat_box, radius=20, fill=(30, 41, 59, 210), outline=(56, 189, 248, 90), width=2)
            
            # Feature Title
            feat_title = clean_text(feat['title'])
            draw.text((content_x + 24, current_y + 18), f"> {feat_title}", fill=COLORS["accent_cyan"], font=feature_title_font)
            
            # Feature Description
            desc_lines = wrap_text(clean_text(feat['desc']), body_font, content_max_w - 48)
            if desc_lines:
                draw.text((content_x + 24, current_y + 72), desc_lines[0], fill=COLORS["primary_text"], font=body_font)
                
            current_y += 164

    # 10. Slide 6 CTA Banner Box
    if "link_display" in slide_data:
        current_y += 16
        cta_box = (content_x, current_y, content_x + content_max_w, current_y + 120)
        draw.rounded_rectangle(cta_box, radius=24, fill=COLORS["accent_green"])
        
        link_font = get_font(32, is_bold=True)
        draw.text((content_x + 32, current_y + 38), clean_text(slide_data["link_display"]), fill=(7, 10, 17), font=link_font)
        current_y += 150

    if "pricing" in slide_data and slide_data["pricing"]:
        price_lines = wrap_text(f"> Fiyat: {slide_data['pricing']}", subtitle_font, content_max_w)
        for line in price_lines:
            draw.text((content_x, current_y), line, fill=COLORS["accent_warning"], font=subtitle_font)
            current_y += 44

    # 11. Footer Section
    footer_y = card_margin_y + card_h - 76
    draw.line([(content_x, footer_y - 20), (content_x + content_max_w, footer_y - 20)], fill=(255, 255, 255, 20), width=1)
    
    # Left Brand Handle
    brand_text = f"{BRAND_HANDLE}"
    draw.text((content_x, footer_y), brand_text, fill=COLORS["accent_cyan"], font=footer_font)
    
    # Right Footer Note
    footer_note = clean_text(slide_data.get("footer", "AI Gücüm • Akıllı Yazılım Rehberi"))
    footer_bbox = footer_font.getbbox(footer_note)
    fw = (footer_bbox[2] - footer_bbox[0]) if footer_bbox else 280
    draw.text((content_x + content_max_w - fw, footer_y), footer_note, fill=COLORS["secondary_text"], font=footer_font)

    # Composite layers
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")

    # Save Output
    output_folder = slide_data.get("output_folder", OUTPUT_DIR)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_filename = f"slide_{slide_data['slide_number']}.png"
    output_path = output_folder / output_filename
    final_img.save(output_path, "PNG", quality=95)
    
    return str(output_path)
