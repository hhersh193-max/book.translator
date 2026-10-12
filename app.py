import os
import requests
from flask import Flask, request, render_template_string, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator
import arabic_reshaper
from bidi.algorithm import get_display
import io
import pytesseract

app = Flask(__name__)

# --- بەشی وەرگێڕانی وێنە ---
def translate_image(image_file):
    img_pil = Image.open(image_file).convert("RGB")
    draw = ImageDraw.Draw(img_pil)
    
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
                        'text': [text],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'right': data['left'][i] + data['width'][i],
                        'bottom': data['top'][i] + data['height'][i]
                    }
                else:
                    lines[key]['text'].append(text)
                    lines[key]['left'] = min(lines[key]['left'], data['left'][i])
                    lines[key]['top'] = min(lines[key]['top'], data['top'][i])
                    lines[key]['right'] = max(lines[key]['right'], data['left'][i] + data['width'][i])
                    lines[key]['bottom'] = max(lines[key]['bottom'], data['top'][i] + data['height'][i])
    
    translator = GoogleTranslator(source='en', target='ku')
    
    for key, line in lines.items():
        original_text = " ".join(line['text'])
        try:
            translated = translator.translate(original_text)
        except:
            translated = original_text
            
        reshaped_text = arabic_reshaper.reshape(translated)
        bidi_text = get_display(reshaped_text)
        
        x1, y1, x2, y2 = line['left'], line['top'], line['right'], line['bottom']
        
        draw.rectangle([x1, y1, x2, y2 + 5], fill=(240, 248, 255))
        draw.text((x1, y1), bidi_text, font=font, fill=(30, 96, 145))
        
    return img_pil

# --- ڕووکاری وێبسایتەکە (HTML/CSS/JS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ku">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>وەرگێڕی ژیر</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e6091;
            --bg: #f0f7fa;
            --card: #ffffff;
        }
        body { 
            font-family: 'Cairo', Tahoma, sans-serif; 
            background-color: var(--bg); 
            margin: 0; 
            padding: 0;
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }
        .app-container {
            width: 100%;
            max-width: 450px;
            background: var(--bg);
            padding: 20px;
            box-sizing: border-box;
        }
        .header {
            text-align: center;
            margin: 20px 0 30px 0;
        }
        .header h1 {
            color: var(--primary);
            font-weight: 800;
            margin: 0;
            font-size: 26px;
        }
        .tabs {
            display: flex;
            background: var(--card);
            border-radius: 30px;
            padding: 5px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }
        .tab-btn {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 0;
            font-family: inherit;
            font-size: 16px;
            font-weight: 600;
            color: #666;
            border-radius: 25px;
            cursor: pointer;
            transition: 0.3s;
        }
        .tab-btn.active {
            background: var(--primary);
            color: white;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .upload-box {
            background: var(--card);
            border: 2px dashed #93c5fd;
            border-radius: 20px;
            padding: 50px 20px;
            text-align: center;
            margin-bottom: 20px;
            position: relative;
        }
        .upload-box input[type="file"] {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0; cursor: pointer;
        }
        .upload-icon {
            font-size: 40px;
            color: var(--primary);
            display: block;
            margin-bottom: 10px;
        }
        
        .btn-main {
            width: 100%;
            background: var(--primary);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 15px;
            font-family: inherit;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(30, 96, 145, 0.3);
            transition: 0.2s;
        }
        .btn-main:active { transform: scale(0.98); }
        
        textarea {
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 15px;
            padding: 15px;
            font-family: inherit;
            font-size: 16px;
            box-sizing: border-box;
            resize: vertical;
            min-height: 120px;
            margin-bottom: 15px;
            background: var(--card);
        }
        .arrow-down {
            text-align: center;
            color: var(--primary);
            font-size: 24px;
            margin: -10px 0 10px 0;
        }
        
        .result-container { margin-top: 20px; text-align: center; }
        .result-container img { max-width: 100%; border-radius: 10px; }
        .loading { display: none; text-align: center; color: var(--primary); margin-top: 15px; font-weight: 600;}
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1>وەرگێڕی ژیر</h1>
        </div>
        
        <!-- دوگمەی بەشەکان -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('image-tab', this)">وێنە</button>
            <button class="tab-btn" onclick="switchTab('file-tab', this)">فایل</button>
            <button class="tab-btn" onclick="switchTab('text-tab', this)">نووسین</button>
        </div>
        
        <!-- ١. بەشی وێنە -->
        <div id="image-tab" class="tab-content active">
            <form id="image-form" onsubmit="submitImage(event)">
                <div class="upload-box">
                    <span class="upload-icon">📷</span>
                    <div style="color: #555; font-weight: 600;">وێنەکە لێرە دابنێ یان هەڵیبژێرە</div>
                    <input type="file" id="image-input" accept="image/*" required onchange="showFileName('image-input', 'image-name')">
                </div>
                <div id="image-name" style="text-align:center; margin-bottom:10px; color:#666;"></div>
                <button type="submit" class="btn-main">وێنەی وەرگێڕدراو بۆ کوردی</button>
            </form>
            <div id="image-loading" class="loading">تکایە چاوەڕێ بکە... خەریکی وەرگێڕانم</div>
            <div id="image-result" class="result-container"></div>
        </div>
        
        <!-- ٢. بەشی فایل -->
        <div id="file-tab" class="tab-content">
            <form id="file-form" onsubmit="submitFile(event)">
                <div class="upload-box">
                    <span class="upload-icon">📄</span>
                    <div style="color: #555; font-weight: 600;">فایلی دەق (.txt) دیاری بکە</div>
                    <input type="file" id="file-input" accept=".txt" required onchange="showFileName('file-input', 'file-name')">
                </div>
                <div id="file-name" style="text-align:center; margin-bottom:10px; color:#666;"></div>
                <button type="submit" class="btn-main">داگرتنی فایلی وەرگێڕدراو</button>
            </form>
            <div id="file-loading" class="loading">خەریکی ئامادەکردنی فایلەم...</div>
        </div>
        
        <!-- ٣. بەشی نووسین -->
        <div id="text-tab" class="tab-content">
            <textarea id="english-text" placeholder="دەقی ئینگلیزی لێرە بنووسە... (English text here)" dir="ltr"></textarea>
            <div class="arrow-down">↓</div>
            <textarea id="kurdish-text" placeholder="دەقی کوردی لێرە دەردەکەوێت..."></textarea>
            <button onclick="translateText()" class="btn-main" id="text-btn">وەرگێڕان بۆ کوردی</button>
        </div>
    </div>

    <!-- سکریپتەکان بۆ کارکردنی بەشەکان -->
    <script>
        function switchTab(tabId, btn) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }
        
        function showFileName(inputId, nameId) {
            const input = document.getElementById(inputId);
            if (input.files.length > 0) {
                document.getElementById(nameId).innerText = "فایلی هەڵبژێردراو: " + input.files[0].name;
            }
        }

        async function submitImage(e) {
            e.preventDefault();
            const fileInput = document.getElementById('image-input');
            const loading = document.getElementById('image-loading');
            const resultDiv = document.getElementById('image-result');
            
            if (fileInput.files.length === 0) return;
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            loading.style.display = 'block';
            resultDiv.innerHTML = '';
            
            try {
                const response = await fetch('/translate_image', { method: 'POST', body: formData });
                if (response.ok) {
                    const blob = await response.blob();
                    const imgUrl = URL.createObjectURL(blob);
                    resultDiv.innerHTML = `<img src="${imgUrl}"><br><br><a href="${imgUrl}" download="Kurdish_Image.jpg" style="color:var(--primary); font-weight:bold; text-decoration:none;">📥 دابەزاندنی وێنەکە</a>`;
                } else {
                    resultDiv.innerHTML = '<span style="color:red">کێشەیەک ڕوویدا.</span>';
                }
            } catch (error) {}
            loading.style.display = 'none';
        }
        
        async function submitFile(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file-input');
            const loading = document.getElementById('file-loading');
            if (fileInput.files.length === 0) return;
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            loading.style.display = 'block';
            
            try {
                const response = await fetch('/translate_file', { method: 'POST', body: formData });
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'Kurdish_' + fileInput.files[0].name;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } else {
                    alert("تکایە دڵنیابە فایلەکەت .txt یە");
                }
            } catch (error) {}
            loading.style.display = 'none';
        }
        
        async function translateText() {
            const text = document.getElementById('english-text').value;
            const btn = document.getElementById('text-btn');
            const resultBox = document.getElementById('kurdish-text');
            
            if (!text.trim()) return;
            btn.innerText = '...چاوەڕێ بکە';
            
            const formData = new FormData();
            formData.append('text', text);
            
            try {
                const response = await fetch('/translate_text', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.translated) resultBox.value = data.translated;
            } catch (error) {
                resultBox.value = "هەڵەیەک ڕوویدا.";
            }
            btn.innerText = 'وەرگێڕان بۆ کوردی';
        }
    </script>
</body>
</html>
"""

# --- بەستەرەکانی سێرڤەر (Routes) ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/translate_image', methods=['POST'])
def translate_image_route():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "فایل نییە", 400
    try:
        result_img = translate_image(request.files['file'])
        img_io = io.BytesIO()
        result_img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return str(e), 500

@app.route('/translate_text', methods=['POST'])
def translate_text_route():
    text = request.form.get('text', '')
    if not text:
        return jsonify({'translated': ''})
    try:
        translator = GoogleTranslator(source='en', target='ku')
        translated = translator.translate(text)
        return jsonify({'translated': translated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/translate_file', methods=['POST'])
def translate_file_route():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "فایل نییە", 400
    try:
        text = request.files['file'].read().decode('utf-8')
        translator = GoogleTranslator(source='en', target='ku')
        chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
        translated_text = "".join([translator.translate(c) + " " for c in chunks])
        
        out_io = io.BytesIO()
        out_io.write(translated_text.encode('utf-8'))
        out_io.seek(0)
        return send_file(out_io, as_attachment=True, download_name=f"kurdish_{request.files['file'].filename}", mimetype='text/plain')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
