import os
import requests
from flask import Flask, request, render_template_string, send_file
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator
import arabic_reshaper
from bidi.algorithm import get_display
import io
import pytesseract

app = Flask(__name__)

def translate_image(image_file):
    # خوێندنەوەی وێنەکە
    img_pil = Image.open(image_file).convert("RGB")
    draw = ImageDraw.Draw(img_pil)
    
    # داگرتنی فۆنتی کوردی (Cairo) ئەگەر بوونی نەبوو
    font_path = "Cairo-Regular.ttf"
    if not os.path.exists(font_path):
        font_url = "https://github.com/googlefonts/cairo/raw/main/fonts/ttf/Cairo-Regular.ttf"
        r = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(r.content)
    
    try:
        font = ImageFont.truetype(font_path, 18)
    except:
        font = ImageFont.load_default()

    # دەرهێنانی دەقەکان لە وێنەکە بە بەکارهێنانی Tesseract
    data = pytesseract.image_to_data(img_pil, output_type=pytesseract.Output.DICT)
    n_boxes = len(data['text'])
    
    lines = {}
    for i in range(n_boxes):
        if int(data['conf'][i]) > 30:
            text = data['text'][i].strip()
            if text:
                key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                if key not in lines:
                    lines[key] = {
