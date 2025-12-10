import network
import socket
import time
from machine import Pin, PWM
import camera

# ============================================
#      CONFIGURACIÓN DE PINES DE MOTORES
# ============================================

MOTOR_FREQ = 1000
MAX_DUTY = 1023  # PWM rango default ESP32

# AJUSTA ESTOS PINES SI TUS MOTORES VAN EN OTROS:
m1a = PWM(Pin(12), freq=MOTOR_FREQ)   # Motor izquierdo A
m1b = PWM(Pin(13), freq=MOTOR_FREQ)   # Motor izquierdo B
m2a = PWM(Pin(14), freq=MOTOR_FREQ)   # Motor derecho A
m2b = PWM(Pin(15), freq=MOTOR_FREQ)   # Motor derecho B

speed_percent = 60  # velocidad inicial 60 %

def _duty_from_speed():
    return int(MAX_DUTY * speed_percent / 100)

def stop():
    m1a.duty(0); m1b.duty(0)
    m2a.duty(0); m2b.duty(0)

# ============================================
#     CORRECCIÓN DE DIRECCIÓN (TU SOLICITUD)
# ============================================

# AHORA ESTO SÍ ES "ADELANTE"
def forward():
    d = _duty_from_speed()
    m1a.duty(0); m1b.duty(d)
    m2a.duty(0); m2b.duty(d)

# Y AHORA ESTO SÍ ES "ATRÁS"
def backward():
    d = _duty_from_speed()
    m1a.duty(d); m1b.duty(0)
    m2a.duty(d); m2b.duty(0)

def left():
    d = _duty_from_speed()
    m1a.duty(0); m1b.duty(d)
    m2a.duty(d); m2b.duty(0)

def right():
    d = _duty_from_speed()
    m1a.duty(d); m1b.duty(0)
    m2a.duty(0); m2b.duty(d)

# ============================================
#              CONTROL DE CÁMARA
# ============================================

camera_enabled = False  # apagada por defecto

def camera_on():
    global camera_enabled
    if camera_enabled:
        return
    try:
        camera.deinit()
    except:
        pass
    camera.init(0)
    camera.framesize(camera.FRAME_QQVGA)  # 160×120 = modo ligero
    try:
        camera.quality(15)
    except:
        pass
    camera_enabled = True
    print("Cámara ON")

def camera_off():
    global camera_enabled
    if not camera_enabled:
        return
    try:
        camera.deinit()
    except:
        pass
    camera_enabled = False
    print("Cámara OFF")

# ============================================
#                 HTML WEB UI
# ============================================

def web_page():
    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Robot WiFi Cam</title>

<style>
body {{
  font-family: Arial;
  background: #111;
  color: #eee;
  text-align: center;
}}

h1 {{ margin-top: 10px; }}

.video-box {{
  margin: 10px auto;
  border: 2px solid #444;
  width: 200px;
  height: 160px;
  background: #000;
}}

.video-box img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}

.btn {{
  width: 100px;
  height: 60px;
  margin: 8px;
  font-size: 18px;
  font-weight: bold;
  border-radius: 10px;
  border: none;
}}

.f {{ background: #2ecc71; }}
.b {{ background: #e74c3c; }}
.l, .r {{ background: #3498db; }}
.s {{ background: #f1c40f; }}

.cam {{
  background: #9b59b6;
  width: 140px;
  height: 45px;
  font-size: 18px;
}}

.slider-container {{
  margin-top: 10px;
  padding: 8px;
  background: #222;
  border-radius: 10px;
  width: 260px;
  margin-left: auto;
  margin-right: auto;
}}

input[type=range] {{
  width: 180px;
}}
</style>

<script>

let camOn = false;

function sendCmd(cmd) {{
  fetch('/?cmd=' + cmd).catch(e => console.log(e));
}}

function startMove(cmd) {{
  sendCmd(cmd);
}}

function stopMove() {{
  sendCmd('S');
}}

function refreshCam() {{
  if (!camOn) return;
  document.getElementById('cam').src = '/capture?rand=' + Date.now();
}}

function setSpeed(val) {{
  document.getElementById('speedValue').innerText = val + '%';
  fetch('/?speed=' + val);
}}

function toggleCam() {{
  camOn = !camOn;
  const btn = document.getElementById('camBtn');
  if (camOn) {{
    btn.innerText = "Cam ON";
    fetch('/?cam=ON');
    refreshCam();
  }} else {{
    btn.innerText = "Cam OFF";
    fetch('/?cam=OFF');
    document.getElementById('cam').src = "";
  }}
}}

window.onload = function() {{
  setInterval(refreshCam, 1200);
}}

</script>
</head>

<body>

<h1>ROBOT WiFi CAM</h1>

<div class="video-box">
  <img id="cam" src="">
</div>

<button id="camBtn" class="btn cam" onclick="toggleCam()">Cam OFF</button>

<div class="slider-container">
  <p>Potencia motores: <span id="speedValue">{speed_percent}%</span></p>
  <input type="range" min="0" max="100" value="{speed_percent}" oninput="setSpeed(this.value)">
</div>

<p>Mantén presionado para mover, suelta para detener.</p>

<div>
  <button class="btn f"
    onmousedown="startMove('F')"
    onmouseup="stopMove()"
    ontouchstart="startMove('F')"
    ontouchend="stopMove()">Fwd</button>
</div>

<div>
  <button class="btn l"
    onmousedown="startMove('L')"
    onmouseup="stopMove()"
    ontouchstart="startMove('L')"
    ontouchend="stopMove()">Left</button>

  <button class="btn s"
    onmousedown="stopMove()"
    onmouseup="stopMove()"
    ontouchstart="stopMove()"
    ontouchend="stopMove()">Stop</button>

  <button class="btn r"
    onmousedown="startMove('R')"
    onmouseup="stopMove()"
    ontouchstart="startMove('R')"
    ontouchend="stopMove()">Right</button>
</div>

<div>
  <button class="btn b"
    onmousedown="startMove('B')"
    onmouseup="stopMove()"
    ontouchstart="startMove('B')"
    ontouchend="stopMove()">Back</button>
</div>

</body>
</html>
"""

# ============================================
#         CONFIGURACIÓN WIFI AP
# ============================================

SSID = "ROBOT-CAM"
PASSWORD = "12345678"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))

print("AP lista → http://192.168.4.1")

stop()

# ============================================
#                SERVIDOR WEB
# ============================================

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    first_line = request.split("\r\n")[0]

    # ---- Captura de imagen ----
    if "GET /capture" in first_line:
        if not camera_enabled:
            conn.sendall(b"HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n")
            conn.close()
            continue
        try:
            buf = camera.capture()
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n")
            conn.sendall(buf)
        except:
            conn.sendall(b"HTTP/1.1 500 Error\r\n\r\n")
        conn.close()
        continue

    # ---- Control de velocidad ----
    if "speed=" in request:
        try:
            val = int(request.split("speed=")[1].split("&")[0])
            speed_percent = max(0, min(100, val))
        except:
            pass

    # ---- Control cámara ----
    if "cam=ON" in request:
        camera_on()
    elif "cam=OFF" in request:
        camera_off()

    # ---- Control movimiento ----
    if "/?cmd=F" in request: forward()
    elif "/?cmd=B" in request: backward()
    elif "/?cmd=L" in request: left()
    elif "/?cmd=R" in request: right()
    elif "/?cmd=S" in request: stop()

    # ---- Página web ----
    webpage = web_page()
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    conn.sendall(webpage)
    conn.close()