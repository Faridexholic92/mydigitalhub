import re
import json
import base64
import requests
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)

# --- KONFIGURASI HACKER ---
def _x(s): return base64.b64decode(s).decode('utf-8')
_H1 = "aHR0cHM6Ly93d3cucmVlbHNob3J0LmNvbS8=" 
_H2 = "TW96aWxsYS81LjAgKExpbnV4OyBBbmRyb2lkIDEwOyBLKSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTI0LjAuMC4wIE1vYmlsZSBTYWZhcmkvNTM3LjM2" 
UA = _x(_H2)
REF = _x(_H1)

SESSION = requests.Session()

# --- LOGIC SCRAPER ---
def get_reelshort_data(url):
    try:
        r = SESSION.get(url, headers={"User-Agent": UA, "Referer": REF}, timeout=10).text
        match = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', r)
        if not match: return None, "Gagal jumpa data rahsia!"

        data = json.loads(match.group(1))
        main = data['props']['pageProps']['data']
        
        info = {
            'id': main['book_id'],
            'title': main['book_title'],
            'slug': url.split("/movie/")[1].split("-"+str(main['book_id']))[0],
            'synopsis': main.get('book_introduction', 'Tiada Data.'),
            'episodes': []
        }

        eps_list = main.get('online_base', [])
        for i, ep in enumerate(eps_list):
            ep_num = i + 1
            ep_api = f"https://www.reelshort.com/episodes/episode-{ep_num}-{info['slug']}-{info['id']}-{ep['chapter_id']}"
            info['episodes'].append({
                'num': ep_num,
                'api_url': ep_api
            })
            
        return info, None
    except Exception as e:
        return None, str(e)

def get_real_stream_link(api_url):
    try:
        res = SESSION.get(api_url, headers={"User-Agent": UA}).text
        match = re.search(r'(https?://[^"]+\.m3u8)', res)
        return match.group(1) if match else None
    except:
        return None

# --- CORS PROXY UNTUK STREAMING ---
@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return "Tiada URL diberikan", 400

    try:
        res = requests.get(url, headers={"User-Agent": UA})
        
        # Jika fail m3u8, kita kena pastikan link dalam tu jadi absolute URL
        if ".m3u8" in url:
            base_url = url.rsplit('/', 1)[0] + '/'
            lines = res.text.split('\n')
            new_lines = []
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    if not line.startswith('http'):
                        line = base_url + line
                new_lines.append(line)
            
            resp = Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        else:
            # Proxy untuk fail .ts
            req = requests.get(url, headers={"User-Agent": UA}, stream=True)
            resp = Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type=req.headers.get('content-type'))
            
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as e:
        return str(e), 500

# --- ROUTE WEBSITE UTAMA ---
@app.route('/', methods=['GET', 'POST'])
def home():
    data = {
        "title": "FARIDEXHOLIC DIGITAL HUB",
        "status": "WAITING FOR TARGET",
        "version": "V18: OWL EDITION"
    }
    
    result = None
    error = None

    if request.method == 'POST':
        target_url = request.form.get('url')
        api_url = request.form.get('api_url')
        
        if target_url and "/movie/" in target_url:
            info, err = get_reelshort_data(target_url)
            if info:
                data["status"] = "TARGET LOCKED"
                result = info
            else:
                error = err
                
        elif api_url:
            # User tekan butang play episod
            stream_link = get_real_stream_link(api_url)
            if stream_link:
                # Kita hantar link stream masuk ke dalam laluan proxy kita
                proxied_link = f"/proxy?url={stream_link}"
                return render_template('player.html', link=proxied_link)
            else:
                error = "Gagal mendapatkan link M3U8."
        else:
            error = "Invalid URL! Mesti mengandungi /movie/"

    return render_template('index.html', data=data, result=result, error=error)

if __name__ == '__main__':
    # Buka port 5000, boleh diakses melalui localhost atau network yang sama
    app.run(host='0.0.0.0', port=5000, debug=True)
