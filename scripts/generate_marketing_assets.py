from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "HeatCheck" / "Assets.xcassets"
MARKETING = ROOT / "MarketingAssets"
SCREENSHOTS = MARKETING / "Screenshots"
ICONS = MARKETING / "Icons"
ICON_SOURCE = ICONS / "app-icon-source-imagegen.png"
GENERATED_ICON_SOURCE = Path(
    r"C:\Users\Windows\.codex\generated_images\019e324f-bfab-77e3-ae40-763fbbf89b73\ig_02b5168bdf206df9016a08f44b704c8191aba242a6e61e01a5.png"
)


PHONE_SIZES = {
    "iphone69": (1320, 2868),
    "iphone65": (1242, 2688),
    "iphone55": (1242, 2208),
}
IPAD_SIZES = {
    "ipad13": (2064, 2752),
    "ipad129": (2048, 2732),
}


SCENES = [
    {
        "name": "01_home",
        "headline": "スマホの熱さを\nひと目で確認",
        "sub": "温度の目安と状態を、女の子がやさしく知らせます。",
        "temp": "34°C",
        "state": "少し熱い",
        "line": "あ、ちょっと暖かい",
        "girl": "heatgirl_warm_03",
        "palette": ((255, 176, 88), (251, 87, 79)),
    },
    {
        "name": "02_alert",
        "headline": "熱くなったら\nすぐお知らせ",
        "sub": "発熱サインを見逃さず、危険になる前に気づけます。",
        "temp": "42°C",
        "state": "暑い",
        "line": "うわ、熱い",
        "girl": "heatgirl_hot_05",
        "palette": ((255, 116, 76), (218, 53, 67)),
    },
    {
        "name": "03_cooling",
        "headline": "冷却アクションで\nすばやく対処",
        "sub": "扇風機、冷房、低電力モードなどをワンタップで記録。",
        "temp": "39°C",
        "state": "回復中",
        "line": "ありがとう",
        "girl": "heatgirl_recovering_02",
        "palette": ((82, 184, 232), (54, 123, 214)),
    },
    {
        "name": "04_tips",
        "headline": "冷却のコツも\nすぐ見られる",
        "sub": "画面の明るさ、ケース、重いアプリなどをチェック。",
        "temp": "45°C",
        "state": "危険",
        "line": "ヤバいヤバい",
        "girl": "heatgirl_critical_04",
        "palette": ((255, 87, 79), (132, 55, 128)),
    },
    {
        "name": "05_expressions",
        "headline": "温度に合わせて\n服と表情が変わる",
        "sub": "涼しい時も、熱い時も、状態に合った反応で知らせます。",
        "temp": "28°C",
        "state": "通常",
        "line": "ちょうどいい",
        "girl": "heatgirl_normal_05",
        "palette": ((255, 194, 103), (74, 154, 232)),
        "expression_grid": True,
    },
]


def font(size, bold=False):
    if bold and Path(r"C:\Windows\Fonts\meiryob.ttc").exists():
        path = r"C:\Windows\Fonts\meiryob.ttc"
    else:
        path = r"C:\Windows\Fonts\meiryo.ttc"
    if not Path(path).exists():
        path = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
    return ImageFont.truetype(path, size=size)


def load_girl(name):
    return crop_visible(Image.open(ASSETS / f"{name}.imageset" / f"{name}.png").convert("RGBA"), padding=8)


def crop_visible(img, padding=0):
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def text_wrap(draw, text, font_obj, max_width):
    rows = []
    for raw in text.split("\n"):
        line = ""
        for ch in raw:
            trial = line + ch
            if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
                line = trial
            else:
                if line:
                    rows.append(line)
                line = ch
        if line:
            rows.append(line)
    return rows


def gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        d.line((0, y, w, y), fill=(r, g, b))
    return img.convert("RGBA")


def rounded_rect(size, radius, fill):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=fill)
    return img


def paste_center(base, overlay, box):
    x, y, w, h = box
    scale = min(w / overlay.width, h / overlay.height)
    resized = overlay.resize((round(overlay.width * scale), round(overlay.height * scale)), Image.Resampling.LANCZOS)
    base.alpha_composite(resized, (round(x + (w - resized.width) / 2), round(y + (h - resized.height) / 2)))


def draw_app_screen(size, scene):
    w, h = size
    screen = gradient(size, scene["palette"][0], scene["palette"][1])
    d = ImageDraw.Draw(screen)

    pad = round(w * 0.07)
    d.text((pad, round(h * 0.07)), "HeatCheck", font=font(round(w * 0.075), bold=True), fill=(255, 255, 255, 245))
    d.text(
        (pad, round(h * 0.19)),
        scene["temp"],
        font=font(round(w * 0.18), bold=True),
        fill=(255, 255, 255, 255),
    )
    d.text((pad, round(h * 0.35)), scene["state"], font=font(round(w * 0.05)), fill=(255, 255, 255, 220))

    girl = load_girl(scene["girl"])
    paste_center(screen, girl, (round(w * 0.06), round(h * 0.34), round(w * 0.88), round(h * 0.38)))

    bubble = rounded_rect((round(w * 0.82), round(h * 0.105)), round(w * 0.035), (255, 255, 255, 58))
    screen.alpha_composite(bubble, (round(w * 0.09), round(h * 0.725)))
    quote = f"「{scene['line']}」"
    d.text((round(w * 0.14), round(h * 0.75)), quote, font=font(round(w * 0.035)), fill=(255, 255, 255, 255))

    labels = [("風", "扇風機"), ("冷", "冷房"), ("省", "省電力")]
    by = round(h * 0.855)
    bw = round((w - pad * 2 - 20) / 3)
    for i, (icon, label) in enumerate(labels):
        bx = pad + i * (bw + 10)
        d.rounded_rectangle((bx, by, bx + bw, by + round(h * 0.075)), radius=round(w * 0.025), fill=(255, 255, 255, 45))
        d.ellipse(
            (
                bx + round(bw * 0.10),
                by + round(h * 0.018),
                bx + round(bw * 0.27),
                by + round(h * 0.056),
            ),
            fill=(255, 255, 255, 52),
        )
        d.text((bx + round(bw * 0.145), by + round(h * 0.018)), icon, font=font(round(w * 0.025), bold=True), fill=(255, 255, 255, 255))
        d.text((bx + round(bw * 0.34), by + round(h * 0.023)), label, font=font(round(w * 0.023), bold=True), fill=(255, 255, 255, 245))

    return screen


def draw_phone_mock(scene, phone_w, phone_h):
    phone = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
    shadow = rounded_rect((phone_w, phone_h), round(phone_w * 0.11), (0, 0, 0, 85)).filter(ImageFilter.GaussianBlur(24))
    phone.alpha_composite(shadow, (0, 18))
    body = rounded_rect((phone_w, phone_h), round(phone_w * 0.11), (28, 31, 42, 255))
    phone.alpha_composite(body, (0, 0))
    inset = round(phone_w * 0.035)
    screen = draw_app_screen((phone_w - inset * 2, phone_h - inset * 2), scene)
    mask = Image.new("L", screen.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, screen.width - 1, screen.height - 1), radius=round(phone_w * 0.08), fill=255)
    phone.alpha_composite(Image.composite(screen, Image.new("RGBA", screen.size), mask), (inset, inset))
    return phone


def draw_expression_strip(base, x, y, width, height):
    names = ["heatgirl_cool_02", "heatgirl_normal_05", "heatgirl_warm_04", "heatgirl_hot_04", "heatgirl_critical_02", "heatgirl_recovering_02"]
    cell_w = width // len(names)
    for i, name in enumerate(names):
        girl = load_girl(name)
        box = (x + i * cell_w + round(cell_w * 0.05), y, round(cell_w * 0.9), height)
        plate = rounded_rect((box[2], height), round(height * 0.22), (255, 255, 255, 45))
        base.alpha_composite(plate, (box[0], y))
        paste_center(base, girl, box)


def create_screenshot(size, scene, out_path):
    w, h = size
    top, bottom = scene["palette"]
    canvas = gradient(size, top, bottom)
    d = ImageDraw.Draw(canvas)

    for i, alpha in enumerate((42, 28, 20)):
        cx = round(w * (0.15 + i * 0.22))
        cy = round(h * (0.15 + i * 0.08))
        r = round(w * (0.45 - i * 0.06))
        glow = Image.new("RGBA", size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, alpha))
        canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(round(w * 0.045))))

    margin = round(w * 0.085)
    headline_font = font(round(w * 0.078), bold=True)
    sub_font = font(round(w * 0.032), bold=True)
    y = round(h * 0.07)
    for line in scene["headline"].split("\n"):
        d.text((margin + 3, y + 3), line, font=headline_font, fill=(0, 0, 0, 55))
        d.text((margin, y), line, font=headline_font, fill=(255, 255, 255, 255))
        y += round(w * 0.096)
    y += round(w * 0.025)
    sub_rows = text_wrap(d, scene["sub"], sub_font, round(w * 0.76))
    if len(sub_rows) > 1 and sub_rows[-1] in {"。", "、"}:
        sub_rows[-2] += sub_rows[-1]
        sub_rows.pop()
    for line in sub_rows:
        d.text((margin + 2, y + 2), line, font=sub_font, fill=(0, 0, 0, 42))
        d.text((margin, y), line, font=sub_font, fill=(255, 255, 255, 232))
        y += round(w * 0.052)

    phone_w = round(w * 0.66) if w < 1500 else round(w * 0.50)
    phone_h = round(phone_w * 2.08)
    phone = draw_phone_mock(scene, phone_w, phone_h)
    px = round((w - phone_w) / 2)
    py = round(h * (0.34 if w < 1500 else 0.32))
    canvas.alpha_composite(phone, (px, py))

    if scene.get("expression_grid"):
        strip_h = round(h * 0.10)
        draw_expression_strip(canvas, margin, round(h * (0.285 if w < 1500 else 0.27)), w - margin * 2, strip_h)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=95)


def create_icon():
    ICONS.mkdir(parents=True, exist_ok=True)
    icon_set = ASSETS / "AppIcon.appiconset"
    icon_set.mkdir(parents=True, exist_ok=True)
    source = ICON_SOURCE if ICON_SOURCE.exists() else GENERATED_ICON_SOURCE
    img = Image.open(source).convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    pix = img.load()
    for y in range(1024):
        for x in range(1024):
            r, g, b = pix[x, y]
            if r < 8 and g < 8 and b < 8:
                t = y / 1023
                pix[x, y] = (
                    int(255 * (1 - t) + 246 * t),
                    int(178 * (1 - t) + 72 * t),
                    int(88 * (1 - t) + 78 * t),
                )
    img.save(ICONS / "app-icon-source-imagegen.png", quality=95)
    img.save(ICONS / "app-icon-1024.png", quality=95)
    img.save(icon_set / "Icon-1024.png", quality=95)
    (icon_set / "Contents.json").write_text(
        json.dumps(
            {
                "images": [{"filename": "Icon-1024.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}],
                "info": {"author": "xcode", "version": 1},
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main():
    create_icon()
    for group, size in {**PHONE_SIZES, **IPAD_SIZES}.items():
        for scene in SCENES:
            create_screenshot(size, scene, SCREENSHOTS / f"{group}_{scene['name']}.png")


if __name__ == "__main__":
    main()
