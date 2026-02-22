import cv2
import numpy as np
from collections import deque
import argparse
import time
import os

# -------- Utils --------
def build_gaussian_pyramid(frame, levels):
    pyr = [frame]
    for _ in range(levels):
        pyr.append(cv2.pyrDown(pyr[-1]))
    return pyr

class TemporalIIRBandpass:
    """IIR band-pass (dos polos) para operar por píxel en la cima de la pirámide."""
    def __init__(self, fmin, fmax, fps):
        self.a_low  = np.exp(-2 * np.pi * fmin / fps)   # high-pass
        self.a_high = np.exp(-2 * np.pi * fmax / fps)   # low-pass
        self.lp = None
        self.hp = None

    def apply(self, x: np.ndarray) -> np.ndarray:
        x = x.astype(np.float32, copy=False)
        if self.lp is None:
            self.lp = x.copy()
            self.hp = x.copy()
        # low-pass a fmax
        self.lp = self.a_high * self.lp + (1.0 - self.a_high) * x
        # high-pass a fmin
        self.hp = self.a_low * self.hp + (1.0 - self.a_low) * x
        return self.lp - self.hp

def central_roi_from_frame(frame, frac_w=0.35, frac_h=0.35):
    H, W = frame.shape[:2]
    w = int(W * frac_w)
    h = int(H * frac_h)
    x = (W - w) // 2
    y = (H - h) // 2
    return (x, y, w, h)

def open_uvc(device_index, width, height, fps):
    # Intento 1: MJPG a la resolución pedida
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  int(width))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    cap.set(cv2.CAP_PROP_FPS,          float(fps))
    if cap.isOpened():
        return cap
    # Intento 2: YUYV a 640x480
    try: cap.release()
    except Exception: pass
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS,          30)
    return cap

def load_face_cascade(custom_path=None):
    if custom_path and os.path.isfile(custom_path):
        return cv2.CascadeClassifier(custom_path)
    # rutas típicas en Ubuntu/Jetson
    candidates = [
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return cv2.CascadeClassifier(p)
    # fallback (vacío, no crashea)
    return cv2.CascadeClassifier()

# -------- Main --------
def main():
    ap = argparse.ArgumentParser(description="EVM con detección de rostro + estabilización/lock")
    # Cámara
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--fps", type=float, default=30.0)

    # EVM
    ap.add_argument("--levels", type=int, default=4)
    ap.add_argument("--alpha", type=float, default=30.0)
    ap.add_argument("--fmin", type=float, default=0.8)   # 48 bpm
    ap.add_argument("--fmax", type=float, default=2.0)   # 120 bpm
    ap.add_argument("--chrom_atten", type=float, default=0.7)

    # ROI / rostro
    ap.add_argument("--roi", type=str, default="", help="x,y,w,h; si se omite se usa rostro o ROI central")
    ap.add_argument("--face", action="store_true", help="usar detección de rostro para definir el ROI")
    ap.add_argument("--face_xml", type=str, default="", help="ruta manual al haarcascade_frontalface_default.xml")
    ap.add_argument("--face_min", type=int, default=80, help="tamaño mínimo de rostro (px)")
    ap.add_argument("--no_face_hold", type=int, default=10, help="frames sin rostro antes de ocultar BPM")

    # Estabilización / bloqueo de lectura
    ap.add_argument("--stable_secs", type=float, default=2.0, help="segundos ESTABLES para bloquear (lock)")
    ap.add_argument("--lock_secs", type=float, default=5.0, help="segundos que se mantiene la lectura fija")
    ap.add_argument("--motion_thresh", type=float, default=0.008, help="umbral movimiento (0..1) en ROI")
    ap.add_argument("--ema", type=float, default=0.7, help="suavizado EMA del bpm (0..1, mayor = más suave)")
    args = ap.parse_args()

    # Cámara (V4L2)
    cap = open_uvc(args.device, args.width, args.height, args.fps)
    if not cap.isOpened():
        print("No pude abrir la cámara (V4L2). Cierra otras apps o prueba 640x480.")
        return

    # Detección de rostro
    face_cascade = load_face_cascade(args.face_xml) if args.face else None
    face_missing_frames = 0
    face_bbox = None  # (x,y,w,h) suavizada

    # ROI manual (si viene)
    roi_manual = None
    if args.roi:
        x, y, w, h = map(int, args.roi.split(","))
        roi_manual = (x, y, w, h)

    # Filtro temporal EVM
    filt = TemporalIIRBandpass(args.fmin, args.fmax, args.fps)
    window_secs = 12
    window = deque(maxlen=int(window_secs * args.fps))

    # Estado
    prev_gray_roi = None
    stable_time = 0.0
    last_t = time.time()
    locked = False
    lock_until = 0.0
    bpm_locked = None
    bpm_smooth = None  # EMA

    font = cv2.FONT_HERSHEY_SIMPLEX
    print("Presiona 'q' para salir.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        now = time.time()
        dt = max(1e-6, now - last_t)
        last_t = now

        frame = cv2.flip(frame, 1)
        frame_f32 = (frame.astype(np.float32) / 255.0)
        H, W = frame.shape[:2]

        # ==== Selección de ROI: rostro -> manual -> central
        roi = None
        face_found = False
        if args.face and face_cascade is not None and not face_cascade.empty():
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # reducir resolución para acelerar detección
            scale = 0.5
            small_gray = cv2.resize(gray_full, (int(W*scale), int(H*scale)))
            faces = face_cascade.detectMultiScale(
                small_gray, scaleFactor=1.1, minNeighbors=5,
                minSize=(args.face_min, args.face_min)
            )
            if len(faces) > 0:
                # escoger el rostro más grande
                fx, fy, fw, fh = max(faces, key=lambda r: r[2]*r[3])
                # re-escalar a coords originales
                fx = int(fx / scale); fy = int(fy / scale)
                fw = int(fw / scale); fh = int(fh / scale)
                # suavizar bbox (EMA)
                if face_bbox is None:
                    face_bbox = (fx, fy, fw, fh)
                else:
                    bx, by, bw, bh = face_bbox
                    alpha = 0.7
                    bx = int(alpha*bx + (1-alpha)*fx)
                    by = int(alpha*by + (1-alpha)*fy)
                    bw = int(alpha*bw + (1-alpha)*fw)
                    bh = int(alpha*bh + (1-alpha)*fh)
                    face_bbox = (bx, by, bw, bh)
                roi = face_bbox
                face_found = True
                face_missing_frames = 0
            else:
                face_missing_frames += 1

        if roi is None and roi_manual is not None:
            roi = roi_manual
        if roi is None:
            roi = central_roi_from_frame(frame_f32, 0.35, 0.35)

        x, y, w, h = roi
        x = max(0, x); y = max(0, y)
        w = min(W - x, w); h = min(H - y, h)
        crop = frame_f32[y:y+h, x:x+w]

        # ====== Detección de movimiento en ROI ======
        gray = cv2.cvtColor((crop * 255.0).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        motion = 0.0
        if prev_gray_roi is not None:
            diff = cv2.absdiff(gray, prev_gray_roi)
            motion = float(np.mean(diff)) / 255.0  # 0..1
        prev_gray_roi = gray
        is_stable = motion < args.motion_thresh

        # ====== EVM en ROI ======
        pyr = build_gaussian_pyramid(crop, args.levels)
        small = pyr[-1].astype(np.float32, copy=False)
        band  = filt.apply(small).astype(np.float32, copy=False)
        amplified = (band * args.alpha).astype(np.float32, copy=False)

        up = amplified
        for l in range(args.levels):
            up = cv2.pyrUp(up, dstsize=(pyr[-2 - l].shape[1], pyr[-2 - l].shape[0]))

        magnified_crop = np.clip(crop + up, 0.0, 1.0)

        # Atenuar croma sobre la imagen final
        if args.chrom_atten < 1.0:
            tmp = (magnified_crop * 255.0).astype(np.float32, copy=False)
            yC, crC, cbC = cv2.split(cv2.cvtColor(tmp, cv2.COLOR_BGR2YCrCb))
            crC *= args.chrom_atten; cbC *= args.chrom_atten
            tmp = cv2.cvtColor(cv2.merge([yC, crC, cbC]), cv2.COLOR_YCrCb2BGR)
            magnified_crop = np.clip(tmp / 255.0, 0.0, 1.0)

        # Ensamblar salida
        out = frame_f32.copy()
        out[y:y+h, x:x+w] = magnified_crop
        vis = (np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)

        # ====== Lógica de cálculo de pulso
        can_measure = True
        msg = None

        if args.face:
            # si pedimos rostro y no hay rostro por varios frames, no medir
            if not face_found and face_missing_frames >= args.no_face_hold:
                can_measure = False
                msg = "No se detecta rostro — coloque su cara en el recuadro"

        if can_measure and is_stable and (not locked):
            gmean = float(np.mean(band[..., 1]))
            window.append(gmean)

            if len(window) == window.maxlen:
                sig = np.asarray(window, dtype=np.float32)
                sig -= sig.mean()
                fft = np.fft.rfft(sig)
                freqs = np.fft.rfftfreq(len(sig), d=1.0/args.fps)
                mask = (freqs >= args.fmin) & (freqs <= args.fmax)
                if np.any(mask):
                    peak = int(np.argmax(np.abs(fft[mask])))
                    f_peak = float(freqs[mask][peak])
                    est_hr = float(f_peak * 60.0)
                    # EMA
                    if 'bpm_smooth' not in locals() or bpm_smooth is None:
                        bpm_smooth = est_hr
                    else:
                        beta = np.clip(args.ema, 0.0, 0.99)
                        bpm_smooth = beta * bpm_smooth + (1.0 - beta) * est_hr

                    # conteo de estabilidad/lock
                    # (solo acumula si realmente estamos midiendo)
                    pass

            # acumular tiempo estable solo si se puede medir
            if is_stable:
                stable_time += dt
                if stable_time >= args.stable_secs and (bpm_smooth is not None) and not locked:
                    locked = True
                    lock_until = now + args.lock_secs
                    bpm_locked = int(round(bpm_smooth))
            else:
                stable_time = 0.0
        else:
            # no medimos (por movimiento o sin rostro)
            stable_time = 0.0

        if locked and now >= lock_until:
            locked = False
            bpm_locked = None

        # ====== Overlay
        color_rect = (0, 255, 0) if (is_stable and can_measure) else (0, 0, 255)
        cv2.rectangle(vis, (x, y), (x+w, y+h), color_rect, 2)

        title = "Coloque su cara dentro del recuadro" if args.face else "Coloque la zona a medir dentro del recuadro"
        cv2.putText(vis, title, (x, max(30, y-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)

        if msg:
            cv2.putText(vis, msg, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2, cv2.LINE_AA)
        elif not is_stable and not locked:
            cv2.putText(vis, "No se mueva, estabilizando...", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2, cv2.LINE_AA)
        elif is_stable and not locked and can_measure:
            faltan = max(0.0, args.stable_secs - stable_time)
            cv2.putText(vis, f"Verificando... {faltan:0.1f}s", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2, cv2.LINE_AA)

        # Lectura (bloqueada o suavizada)
        if locked and bpm_locked is not None:
            cv2.putText(vis, f"{bpm_locked} bpm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3, cv2.LINE_AA)
            restante = lock_until - now
            cv2.putText(vis, f"Lectura fijada {restante:0.0f}s", (20, vis.shape[0]-20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
        elif 'bpm_smooth' in locals() and bpm_smooth is not None and can_measure:
            cv2.putText(vis, f"{int(round(bpm_smooth))} bpm", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,200,0), 2, cv2.LINE_AA)

        # Footer info
        cv2.putText(vis, f"EVM alpha={args.alpha} [{args.fmin}-{args.fmax}]Hz  L={args.levels}",
                    (20, vis.shape[0]-50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(vis, f"mov={motion:0.3f}  estable> {args.motion_thresh:0.3f}",
                    (20, vis.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 1, cv2.LINE_AA)

        cv2.imshow("Eulerian Video Magnification (q=salir)", vis)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
