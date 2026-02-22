"""
EulerianProcessorModule - Módulo de procesamiento de magnificación euleriana.
Amplifica movimientos sutiles y variaciones de color en video.

Implementación completa con:
- ROI central (o configurable)
- Filtro IIR temporal en tiempo real (O(1) por frame)
- Detección de movimiento en el ROI
- Cálculo de BPM vía FFT
- Estabilización y bloqueo de lectura
- Overlays informativos (idénticos a prueba.py)
"""

import cv2
import numpy as np
from collections import deque
from typing import Any, Dict, Optional
import time

import sys
sys.path.append('src')

from core.base_device import BaseDevice


class _TemporalIIRBandpass:
    """Filtro IIR pasa-banda temporal de dos polos.
    Opera sobre la cima de la pirámide gaussiana, frame a frame (O(1))."""

    def __init__(self, fmin: float, fmax: float, fps: float):
        self.a_low = np.exp(-2.0 * np.pi * fmin / fps)   # high-pass
        self.a_high = np.exp(-2.0 * np.pi * fmax / fps)  # low-pass
        self.lp: Optional[np.ndarray] = None
        self.hp: Optional[np.ndarray] = None

    def apply(self, x: np.ndarray) -> np.ndarray:
        x = x.astype(np.float32, copy=False)
        if self.lp is None:
            self.lp = x.copy()
            self.hp = x.copy()
        self.lp = self.a_high * self.lp + (1.0 - self.a_high) * x
        self.hp = self.a_low * self.hp + (1.0 - self.a_low) * x
        return self.lp - self.hp

    def reset(self):
        self.lp = None
        self.hp = None


def _build_gaussian_pyramid(frame: np.ndarray, levels: int) -> list:
    """Construye pirámide gaussiana."""
    pyr = [frame]
    for _ in range(levels):
        pyr.append(cv2.pyrDown(pyr[-1]))
    return pyr


def _central_roi(frame: np.ndarray, frac_w: float = 0.35,
                 frac_h: float = 0.35):
    """Calcula ROI central del frame."""
    H, W = frame.shape[:2]
    w = int(W * frac_w)
    h = int(H * frac_h)
    x = (W - w) // 2
    y = (H - h) // 2
    return x, y, w, h


class EulerianProcessorModule(BaseDevice):
    """
    Módulo de magnificación euleriana de video (tiempo real) con
    detección de BPM, ROI, estabilización y overlays.

    Replica la funcionalidad visual completa de prueba.py dentro
    del sistema modular PureVision.
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        super().__init__(device_id, config)

        # --- Parámetros EVM ---
        self.amplification_factor = config.get("amplification_factor", 30)
        self.low_freq = config.get("low_freq", 0.8)
        self.high_freq = config.get("high_freq", 2.0)
        self.pyramid_levels = config.get("pyramid_levels", 4)
        self.fps = config.get("fps", 30)
        self.chrom_atten = config.get("chrom_atten", 0.7)

        # --- ROI ---
        self.roi_frac_w = config.get("roi_frac_w", 0.35)
        self.roi_frac_h = config.get("roi_frac_h", 0.35)

        # --- Estabilización / BPM ---
        self.motion_thresh = config.get("motion_thresh", 0.008)
        self.stable_secs = config.get("stable_secs", 2.0)
        self.lock_secs = config.get("lock_secs", 5.0)
        self.ema_beta = config.get("ema", 0.7)
        self.window_secs = config.get("window_secs", 12)
        self.flip_horizontal = config.get("flip_horizontal", True)

        # --- Estado interno (se inicializa en initialize) ---
        self.temporal_filter: Optional[_TemporalIIRBandpass] = None
        self.window: Optional[deque] = None
        self.prev_gray_roi: Optional[np.ndarray] = None
        self.stable_time = 0.0
        self.last_t = 0.0
        self.locked = False
        self.lock_until = 0.0
        self.bpm_locked: Optional[int] = None
        self.bpm_smooth: Optional[float] = None
        self.motion = 0.0
        self.is_stable = False

        self.frame_count = 0
        self.processed_frames = 0

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def initialize(self) -> bool:
        try:
            self.logger.info("Inicializando procesador euleriano (IIR tiempo real + BPM)")
            self.logger.info(
                f"Configuración: alpha={self.amplification_factor}, "
                f"freq=[{self.low_freq}-{self.high_freq}]Hz, "
                f"levels={self.pyramid_levels}"
            )

            if self.amplification_factor <= 0:
                self.logger.error("Factor de amplificación debe ser positivo")
                return False
            if self.low_freq >= self.high_freq:
                self.logger.error("Frecuencia baja debe ser menor que la alta")
                return False

            self.temporal_filter = _TemporalIIRBandpass(
                self.low_freq, self.high_freq, self.fps
            )
            self.window = deque(maxlen=int(self.window_secs * self.fps))
            self.last_t = time.time()

            return True
        except Exception as e:
            self.logger.error(f"Error al inicializar procesador: {e}")
            return False

    def start(self) -> bool:
        self.logger.info("Procesador euleriano iniciado")
        return True

    def stop(self) -> bool:
        self.logger.info("Procesador euleriano detenido")
        return True

    # ------------------------------------------------------------------
    # Procesamiento principal
    # ------------------------------------------------------------------
    def process(self, data: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """Procesa un frame: EVM en ROI + BPM + overlays.

        Devuelve el frame uint8 listo para mostrar (con todos los overlays).
        """
        if data is None:
            return None

        try:
            self.frame_count += 1
            now = time.time()
            dt = max(1e-6, now - self.last_t)
            self.last_t = now

            # Flip horizontal (espejo) como prueba.py
            frame = cv2.flip(data, 1) if self.flip_horizontal else data.copy()
            frame_f32 = frame.astype(np.float32) / 255.0
            H, W = frame.shape[:2]

            # ---- ROI central ----
            x, y, w, h = _central_roi(frame_f32, self.roi_frac_w, self.roi_frac_h)
            x = max(0, x)
            y = max(0, y)
            w = min(W - x, w)
            h = min(H - y, h)
            crop = frame_f32[y:y+h, x:x+w]

            # ---- Detección de movimiento en ROI ----
            gray = cv2.cvtColor(
                (crop * 255.0).astype(np.uint8), cv2.COLOR_BGR2GRAY
            )
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            self.motion = 0.0
            if self.prev_gray_roi is not None:
                diff = cv2.absdiff(gray, self.prev_gray_roi)
                self.motion = float(np.mean(diff)) / 255.0
            self.prev_gray_roi = gray
            self.is_stable = self.motion < self.motion_thresh

            # ---- EVM en ROI ----
            pyr = _build_gaussian_pyramid(crop, self.pyramid_levels)
            small = pyr[-1].astype(np.float32, copy=False)
            band = self.temporal_filter.apply(small).astype(np.float32, copy=False)
            amplified = (band * self.amplification_factor).astype(np.float32, copy=False)

            up = amplified
            for lvl in range(self.pyramid_levels):
                up = cv2.pyrUp(
                    up, dstsize=(pyr[-2 - lvl].shape[1], pyr[-2 - lvl].shape[0])
                )

            magnified_crop = np.clip(crop + up, 0.0, 1.0)

            # Atenuar croma
            if self.chrom_atten < 1.0:
                tmp = (magnified_crop * 255.0).astype(np.float32, copy=False)
                yC, crC, cbC = cv2.split(
                    cv2.cvtColor(tmp, cv2.COLOR_BGR2YCrCb)
                )
                crC *= self.chrom_atten
                cbC *= self.chrom_atten
                tmp = cv2.cvtColor(
                    cv2.merge([yC, crC, cbC]), cv2.COLOR_YCrCb2BGR
                )
                magnified_crop = np.clip(tmp / 255.0, 0.0, 1.0)

            # Ensamblar frame de salida
            out = frame_f32.copy()
            out[y:y+h, x:x+w] = magnified_crop
            vis = (np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)

            # ---- Lógica BPM / estabilización ----
            self._update_bpm(band, dt, now)

            # ---- Overlays ----
            vis = self._draw_overlays(vis, x, y, w, h, now)

            self.processed_frames += 1
            return vis

        except Exception as e:
            self.logger.error(f"Error al procesar frame: {e}")
            return data

    # ------------------------------------------------------------------
    # BPM
    # ------------------------------------------------------------------
    def _update_bpm(self, band: np.ndarray, dt: float, now: float):
        """Calcula BPM con FFT y lógica de estabilización/lock."""
        if self.is_stable and not self.locked:
            gmean = float(np.mean(band[..., 1]))
            self.window.append(gmean)

            if len(self.window) == self.window.maxlen:
                sig = np.asarray(self.window, dtype=np.float32)
                sig -= sig.mean()
                fft = np.fft.rfft(sig)
                freqs = np.fft.rfftfreq(len(sig), d=1.0 / self.fps)
                mask = (freqs >= self.low_freq) & (freqs <= self.high_freq)
                if np.any(mask):
                    peak = int(np.argmax(np.abs(fft[mask])))
                    f_peak = float(freqs[mask][peak])
                    est_hr = float(f_peak * 60.0)
                    if self.bpm_smooth is None:
                        self.bpm_smooth = est_hr
                    else:
                        beta = np.clip(self.ema_beta, 0.0, 0.99)
                        self.bpm_smooth = beta * self.bpm_smooth + (1.0 - beta) * est_hr

            # Acumular estabilidad
            self.stable_time += dt
            if (self.stable_time >= self.stable_secs
                    and self.bpm_smooth is not None
                    and not self.locked):
                self.locked = True
                self.lock_until = now + self.lock_secs
                self.bpm_locked = int(round(self.bpm_smooth))
        else:
            if not self.locked:
                self.stable_time = 0.0

        # Expirar lock
        if self.locked and now >= self.lock_until:
            self.locked = False
            self.bpm_locked = None

    # ------------------------------------------------------------------
    # Overlays
    # ------------------------------------------------------------------
    def _draw_overlays(self, vis: np.ndarray, x: int, y: int,
                       w: int, h: int, now: float) -> np.ndarray:
        """Dibuja rectángulo ROI, textos de estado y BPM (igual que prueba.py)."""
        # Rectángulo ROI
        color_rect = (0, 255, 0) if self.is_stable else (0, 0, 255)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color_rect, 2)

        # Título sobre ROI
        title = "Coloque la zona a medir dentro del recuadro"
        cv2.putText(vis, title, (x, max(30, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
                    cv2.LINE_AA)

        # Mensajes de estado
        if not self.is_stable and not self.locked:
            cv2.putText(vis, "No se mueva, estabilizando...", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2,
                        cv2.LINE_AA)
        elif self.is_stable and not self.locked:
            faltan = max(0.0, self.stable_secs - self.stable_time)
            cv2.putText(vis, f"Verificando... {faltan:0.1f}s", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2,
                        cv2.LINE_AA)

        # BPM
        if self.locked and self.bpm_locked is not None:
            cv2.putText(vis, f"{self.bpm_locked} bpm", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3,
                        cv2.LINE_AA)
            restante = self.lock_until - now
            cv2.putText(
                vis,
                f"Lectura fijada {restante:0.0f}s",
                (20, vis.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
                cv2.LINE_AA,
            )
        elif self.bpm_smooth is not None:
            cv2.putText(vis, f"{int(round(self.bpm_smooth))} bpm", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 0), 2,
                        cv2.LINE_AA)

        # Footer: parámetros EVM y movimiento
        cv2.putText(
            vis,
            f"EVM alpha={self.amplification_factor} "
            f"[{self.low_freq}-{self.high_freq}]Hz  L={self.pyramid_levels}",
            (20, vis.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,
        )
        cv2.putText(
            vis,
            f"mov={self.motion:0.3f}  estable> {self.motion_thresh:0.3f}",
            (20, vis.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA,
        )

        return vis

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def cleanup(self) -> None:
        if self.temporal_filter:
            self.temporal_filter.reset()
        self.logger.info("Recursos del procesador liberados")

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "eulerian_processor",
            "amplification_factor": self.amplification_factor,
            "frequency_range": f"{self.low_freq}-{self.high_freq} Hz",
            "pyramid_levels": self.pyramid_levels,
            "chrom_atten": self.chrom_atten,
            "frames_received": self.frame_count,
            "frames_processed": self.processed_frames,
            "bpm_smooth": self.bpm_smooth,
            "bpm_locked": self.bpm_locked,
            "locked": self.locked,
        }

    def set_amplification(self, factor: float) -> None:
        old = self.amplification_factor
        self.amplification_factor = factor
        self.logger.info(f"Factor de amplificación cambiado: {old} -> {factor}")

    def set_frequency_range(self, low_freq: float, high_freq: float) -> None:
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.temporal_filter = _TemporalIIRBandpass(low_freq, high_freq, self.fps)
        self.logger.info(f"Rango de frecuencias cambiado: {low_freq}-{high_freq} Hz")
