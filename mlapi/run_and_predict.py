# run_and_predict.py
import subprocess, sys, time, json, pathlib, signal
from urllib.parse import urljoin

import requests

HOST = "127.0.0.1"
PORT = 801
BASE = f"http://{HOST}:{PORT}/"
HEALTH_URL = urljoin(BASE, "api/v1/health/")
PREDICT_URL = urljoin(BASE, "api/v1/predict/")
PAYLOAD_PATH = pathlib.Path("_debug/predict_template.json")

def wait_for_health(url: str, timeout: float = 45.0, interval: float = 0.7) -> None:
    start = time.time()
    last_err = None
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                return
        except Exception as e:
            last_err = e
        time.sleep(interval)
    raise TimeoutError(f"Health check timed out after {timeout}s. Last error: {last_err}")

def main():
    # شغّل السيرفر
    print(f"🚀 starting Django dev server at {BASE} ...")
    server = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"{HOST}:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # استنى /health
        print("⏳ waiting for /health ...")
        wait_for_health(HEALTH_URL)
        print("✅ health is OK")

        # اقرأ الـ JSON
        if not PAYLOAD_PATH.exists():
            raise FileNotFoundError(f"payload file not found: {PAYLOAD_PATH}")
        data = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))

        # ابعت /predict
        print(f"📤 POST {PREDICT_URL}")
        resp = requests.post(PREDICT_URL, json=data, timeout=20)
        print("🔢 status:", resp.status_code)
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype.lower():
            try:
                print("🧾 response JSON:", json.dumps(resp.json(), ensure_ascii=False, indent=2))
            except Exception:
                print("🧾 response text:", resp.text)
        else:
            print("🧾 response text:", resp.text)

    finally:
        # اقفل السيرفر بنظافة
        print("🛑 stopping server ...")
        try:
            # جرّب SIGINT (CTRL+C)
            server.send_signal(signal.CTRL_BREAK_EVENT if hasattr(signal, "CTRL_BREAK_EVENT") else signal.SIGINT)
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
        except Exception:
            server.kill()

        # اطبع آخر سطور من لوج السيرفر (اختياري)
        try:
            out = server.stdout.read()
            if out:
                tail = "\n".join(out.splitlines()[-20:])
                print("\n--- server log (tail) ---\n" + tail)
        except Exception:
            pass

if __name__ == "__main__":
    main()
