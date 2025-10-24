from dataclasses import dataclass
from typing import Optional, Tuple, Sequence, Dict, Union, List, cast
import urllib.parse
import requests
import numpy as np
import cv2
from pathlib import Path

cv2.setUseOptimized(True)
try:
    cv2.setNumThreads(2)  # teste 1 ou 2
except Exception:
    pass


@dataclass
class ResultadoDeteccao:
    encontrou: bool
    valor: float
    posicao: Optional[Tuple[int, int]]
    escala: Optional[float]
    url_analisada: Optional[str] = None
    template_usado: Optional[str] = None


class VerificadorImagemUseBar:
    _cache_templates_gray: Dict[str, np.ndarray] = {}
    _cache_listagem_pasta: Dict[Tuple[str, Tuple[str, ...]], List[Path]] = {}

    def __init__(
            self,
            base_url: str = "https://www.mucabrasil.com.br/forum/userbar.php",
            limiar: float = 0.80,
            timeout_download: int = 5,
            user_agent: Optional[str] = "Mozilla/5.0 (compatible; VerificadorImagemRemota/1.0)"
    ):
        self.base_url = base_url
        self.limiar = float(limiar)
        self.timeout_download = int(timeout_download)
        self.user_agent = user_agent

    # -------- util ----------
    def _baixar_imagem(self, url: str) -> Optional[np.ndarray]:
        try:
            headers = {"User-Agent": self.user_agent} if self.user_agent else {}
            r = requests.get(url, headers=headers, timeout=self.timeout_download)
            r.raise_for_status()
            data = np.frombuffer(r.content, np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
            if img is None:
                return None
            if img.ndim == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            print(f"[ERRO] Falha ao baixar imagem: {e}")
            return None

    def _carregar_template_gray(self, template_path: str) -> Optional[np.ndarray]:
        arr = self._cache_templates_gray.get(template_path)
        if arr is not None:
            return arr
        tpl = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if tpl is None:
            print(f"[ERRO] Template inválido: {template_path}")
            return None
        if tpl.ndim == 3 and tpl.shape[2] == 4:
            tpl = cv2.cvtColor(tpl, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
        self._cache_templates_gray[template_path] = gray
        return gray

    def _listar_templates(self, pasta: Path, extensoes: Sequence[str]) -> List[Path]:
        key = (str(pasta.resolve()), tuple(extensoes))
        cached = self._cache_listagem_pasta.get(key)
        if cached is not None:
            return cached

        arquivos: List[Path] = []
        for ext in extensoes:
            arquivos.extend(pasta.glob(f"*{ext}"))
            if ext.lower() != ext:
                arquivos.extend(pasta.glob(f"*{ext.lower()}"))
            if ext.upper() != ext:
                arquivos.extend(pasta.glob(f"*{ext.upper()}"))

        # remove duplicados, ordena e mantém como LISTA
        arquivos = list(sorted(set(arquivos)))
        self._cache_listagem_pasta[key] = arquivos
        return arquivos

    # -------- filtro 1D rápido (projeção vertical) ----------
    import numpy as np

    @staticmethod
    def _roll_ssd_1d(img_cols: np.ndarray, tpl_cols: np.ndarray) -> np.ndarray:
        """
        SSD 1D por deslocamento entre a projeção vertical da imagem (img_cols)
        e do template (tpl_cols). Retorna (iw - tw + 1,) com valores menores = melhor.
        Implementação sem usar atributos/métodos do ndarray nas partes sensíveis ao type checker.
        """
        # Garante 1D float32 sem usar .ravel()
        img_cols = np.reshape(np.asarray(img_cols, dtype=np.float32), (-1,))
        tpl_cols = np.reshape(np.asarray(tpl_cols, dtype=np.float32), (-1,))

        # >>> usa função np.shape, evitando ".shape"
        tw: int = int(np.shape(tpl_cols)[0])

        # sum(I^2) por janela via prefix-sum (só funções do numpy)
        I2 = np.multiply(img_cols, img_cols)
        ps = np.concatenate((
            np.array([0.0], dtype=np.float64),
            np.cumsum(I2, dtype=np.float64)
        ))
        sumI2_win = ps[tw:] - ps[:-tw]  # (iw - tw + 1,)

        # correlação 1D
        cross = np.convolve(img_cols, tpl_cols[::-1], mode="valid")

        # >>> resultado escalar com cast estático p/ agradar o type checker
        sumT2_np = np.sum(np.multiply(tpl_cols, tpl_cols), dtype=np.float64)
        sumT2: float = cast(float, sumT2_np)

        ssd = sumI2_win - 2.0 * cross + sumT2
        return np.asarray(ssd, dtype=np.float32)

    # -------- API ----------
    def verificar_pasta(
            self,
            nome: str,
            pasta_templates: str | Path,
            extensoes: Sequence[str] = (".png", ".jpg", ".jpeg"),
            debug: bool = False,
            # dica: ajuste roi_x=(L,R) se você sabe onde aparece (ex.: (0, 210))
            roi_x: Optional[Tuple[int, int]] = None,
            # quantos candidatos do filtro 1D ir para o matchTemplate
            top_k: int = 3,
            # quantas colunas extras pegar ao redor do candidato para o match fino
            pad_cols: int = 8,
    ) -> bool:
        pasta = Path(pasta_templates)
        if not pasta.exists() or not pasta.is_dir():
            if debug: print(f"[DEBUG] Pasta inválida: {pasta}")
            return False

        arquivos = self._listar_templates(pasta, extensoes)
        if not arquivos:
            if debug: print(f"[DEBUG] Nenhum template encontrado em {pasta} com {extensoes}")
            return False

        url = f"{self.base_url}?n={urllib.parse.quote_plus(nome)}"
        img = self._baixar_imagem(url)
        if img is None:
            return False

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ih, iw = img_gray.shape[:2]  # esperado 20 x 350

        # ROI horizontal (opcional)
        x0, x1 = 0, iw
        if roi_x is not None:
            x0 = max(0, int(roi_x[0]))
            x1 = min(iw, int(roi_x[1]))
            if x1 - x0 < 8:  # proteção
                x0, x1 = 0, iw
        img_roi = img_gray[:, x0:x1]
        iw_roi = img_roi.shape[1]

        # projeção vertical da imagem (soma das colunas)
        proj_img = img_roi.sum(axis=0)  # shape: (iw_roi,)

        melhor = ResultadoDeteccao(False, 0.0, None, 1.0, url, None)

        for arq in arquivos:
            tpl_gray = self._carregar_template_gray(str(arq))
            if tpl_gray is None:
                continue

            th, tw = tpl_gray.shape[:2]
            if th > ih or tw > iw_roi or th < 6 or tw < 6:
                if debug:
                    print(f"[DEBUG] {arq.name} fora do range (tpl {tw}x{th}, imgROI {iw_roi}x{ih})")
                continue

            # --- Estágio 1: filtro 1D barato (usa só soma por coluna) ---
            proj_tpl = tpl_gray.sum(axis=0)  # shape: (tw,)
            ssd = self._roll_ssd_1d(proj_img, proj_tpl)  # shape: (iw_roi - tw + 1,)

            # pega os melhores candidatos (menor SSD)
            if ssd.size <= 0:
                continue
            k = min(top_k, int(ssd.size))
            cand_x_local = np.argpartition(ssd, k - 1)[:k]  # k menores (desordenados)
            # ordena por qualidade
            cand_x_local = cand_x_local[np.argsort(ssd[cand_x_local])]

            # --- Estágio 2: matchTemplate só ao redor dos candidatos ---
            hit = False
            for xl in cand_x_local:
                # converte x local (ROI) para x global
                xg = int(xl) + x0

                # recorta uma faixa estreita ao redor do candidato
                xa = max(xg - pad_cols, 0)
                xb = min(xg + tw + pad_cols, iw)
                sub = img_gray[:, xa:xb]

                # se a faixa ainda cabe:
                if sub.shape[1] < tw or sub.shape[0] < th:
                    continue

                res = cv2.matchTemplate(sub, tpl_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if debug:
                    print(f"[DEBUG] {arq.name} x≈{xg} val={max_val:.4f} (janela {xa}:{xb})")

                if max_val >= self.limiar:
                    return True

                if max_val > melhor.valor:
                    # ajusta pos global
                    melhor = ResultadoDeteccao(
                        False, float(max_val),
                        (int(max_loc[0] + xa), int(max_loc[1])),
                        1.0,
                        url_analisada=url,
                        template_usado=str(arq)
                    )

        return melhor.encontrou
