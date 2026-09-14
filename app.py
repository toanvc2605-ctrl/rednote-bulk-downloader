import os, re, json, uuid, zipfile, shutil
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, HttpUrl
import httpx

BASE = Path(__file__).parent
DOWNLOADS = BASE / 'downloads'
DOWNLOADS.mkdir(exist_ok=True)

app = FastAPI(title='RedNote Bulk Video Downloader')
jobs = {}

class ScanRequest(BaseModel):
    profile_url: HttpUrl
    max_posts: int = 20

class DownloadRequest(BaseModel):
    job_id: str
    indexes: list[int] | None = None

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RedNote Bulk Video Downloader</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding-top: 50px; }
        .main-card { border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container justify-content-center" style="max-width: 600px;">
        <div class="card main-card p-4 bg-white">
            <h2 class="text-center text-danger mb-4">🎈 RedNote Video Downloader</h2>
            <div class="mb-3">
                <label class="form-label font-weight-bold">Nhập Link Bài Viết Hoặc Profile RedNote:</label>
                <input type="text" id="profileUrl" class="form-control" placeholder="https://xiaohongshu.com... hoặc https://xiaohongshu.com...">
            </div>
            <button id="scanBtn" class="btn btn-danger w-100 py-2">🔍 Bắt Đầu Tải Video</button>
            
            <div id="loading" class="text-center my-4 d-none">
                <div class="spinner-border text-danger" role="status"></div>
                <p class="mt-2 text-secondary">Hệ thống đang tải dữ liệu video, vui lòng đợi...</p>
            </div>

            <div id="resultSection" class="mt-4 d-none text-center">
                <h4 class="text-success">Tìm thấy tệp video thành công!</h4>
                <button id="downloadBtn" class="btn btn-success mt-3 px-5 py-2">⚡ Tải File Về Máy Mac</button>
            </div>
        </div>
    </div>

    <script>
        let currentJobId = "";
        document.getElementById('scanBtn').onclick = async () => {
            const profileUrl = document.getElementById('profileUrl').value;
            if(!profileUrl) return alert("Vui lòng điền link!");
            document.getElementById('loading').classList.remove('d-none');
            document.getElementById('resultSection').classList.add('d-none');
            try {
                const res = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ profile_url: profileUrl })
                });
                if(!res.ok) throw new Error(await res.text());
                const data = await res.json();
                currentJobId = data.job_id;
                document.getElementById('resultSection').classList.remove('d-none');
            } catch(e) {
                alert("Có lỗi xảy ra hoặc link không hợp lệ.");
            } finally {
                document.getElementById('loading').classList.add('d-none');
            }
        };

        document.getElementById('downloadBtn').onclick = async () => {
            if(!currentJobId) return;
            window.location.href = `/api/download?job_id=${currentJobId}`;
        };
    </script>
</body>
</html>
"""

@app.get('/', response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=HTML_INTERFACE, status_code=200)

@app.post('/api/scan')
async def scan(req: ScanRequest):
    job_id = uuid.uuid4().hex
    url_str = str(req.profile_url)
    
    # Sử dụng API chia sẻ mở để quét link trực tiếp không cần trình duyệt ảo
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            res = await client.get(url_str, headers=headers)
            html = res.text
            
            # Tìm link video dạng MP4 trong mã nguồn trang bằng Regex công thức
            match = re.search(r'"video":\s*\{\s*"url":\s*"([^"]+)"', html)
            if not match:
                match = re.search(r'http[s]?://[^"\s]+\.mp4', html)
                
            if match:
                video_url = match.group(1).replace(r'\u002F', '/') if '\\u002F' in match.group(0) else match.group(0)
                jobs[job_id] = video_url
                return {'job_id': job_id}
        except Exception:
            pass
    raise HTTPException(400, 'Không tìm thấy video công khai trong liên kết này.')

@app.get('/api/download')
async def download(job_id: str):
    video_url = jobs.get(job_id)
    if not video_url: raise HTTPException(404,'Liên kết hết hạn.')
    path = DOWNLOADS / f"{job_id}.mp4"
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        r = await client.get(video_url)
        path.write_bytes(r.content)
   return FileResponse(zip_path, filename='rednote_videos_bulk.zip', media_type='application/zip')
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

