import re
import json
import base64
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# --- KONFIGURASI HACKER ---
def _x(s): return base64.b64decode(s).decode('utf-8')
_H1 = "aHR0cHM6Ly93d3cucmVlbHNob3J0LmNvbS8=" 
_H2 = "TW96aWxsYS81LjAgKExpbnV4OyBBbmRyb2lkIDEwOyBLKSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTI0LjAuMC4wIE1vYmlsZSBTYWZhcmkvNTM3LjM2" 
UA = _x(_H2)
REF = _x(_H1)

SESSION = requests.Session()

# --- LOGIC DARI SCRIPT KAU (Dipermudahkan untuk Web) ---
def get_reelshort_data(url):
    try:
        # 1. Tembus Link Utama
        r = SESSION.get(url, headers={"User-Agent": UA, "Referer": REF}, timeout=10).text
        
        # 2. Cari Data Tersembunyi (JSON)
        match = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', r)
        if not match:
            return None, "Gagal jumpa data rahsia!"

        data = json.loads(match.group(1))
        main = data['props']['pageProps']['data']
        
        # 3. Ambil Info Drama
        info = {
            'id': main['book_id'],
            'title': main['book_title'],
            'slug': url.split("/movie/")[1].split("-"+str(main['book_id']))[0],
            'synopsis': main.get('book_introduction', 'Tiada Data.'),
            'episodes': []
        }

        # 4. Generate Link M3U8 untuk setiap episod
        eps_list = main.get('online_base', [])
        for i, ep in enumerate(eps_list):
            ep_num = i + 1
            # URL API untuk curi stream link
            ep_api = f"https://www.reelshort.com/episodes/episode-{ep_num}-{info['slug']}-{info['id']}-{ep['chapter_id']}"
            
            # Kita simpan link API ni, nanti user tekan baru kita request (supaya server tak berat)
            info['episodes'].append({
                'num': ep_num,
                'api_url': ep_api
            })
            
        return info, None
    except Exception as e:
        return None, str(e)

def get_real_stream_link(api_url):
    try:
        # Request ke API ReelShort untuk dapatkan M3U8
        res = SESSION.get(api_url, headers={"User-Agent": UA}).text
        match = re.search(r'(https?://[^"]+\.m3u8)', res)
        return match.group(1) if match else None
    except:
        return None

# --- ROUTE WEBSITE ---

@app.route('/', methods=['GET', 'POST'])
def home():
    data = {
        "title": "SYSTEM BREACH: READY",
        "status": "WAITING FOR TARGET",
        "version": "V19: Web Extractor"
    }
    
    result = None
    error = None

    if request.method == 'POST':
        target_url = request.form.get('url')
        if target_url and "/movie/" in target_url:
            info, err = get_reelshort_data(target_url)
            if info:
                data["status"] = "TARGET LOCKED"
                result = info
            else:
                error = err
        elif request.form.get('api_url'):
            # Ini kalau user tekan butang "GET LINK" pada episod
            stream_link = get_real_stream_link(request.form.get('api_url'))
            return render_template('player.html', link=stream_link)
        else:
            error = "Invalid URL! Must contain /movie/"

    return render_template('index.html', data=data, result=result, error=error)

if __name__ == '__main__':
    app.run(debug=True)
