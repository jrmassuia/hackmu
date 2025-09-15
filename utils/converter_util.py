from datetime import datetime

import cv2
import numpy as np
# from pytesseract import pytesseract
#
# pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def stringToDateTime(date_time_str):
    return datetime.strptime(date_time_str[0:-1], '%Y-%m-%dT%H:%M:%S.%f')




# def processar_imagem_para_obter_valorOLD(img, salvar_imagem=False, caminho_salvar='imagem_processada.png'):
#     """Pré-processa a imagem, salva a imagem processada (opcionalmente) e extrai o texto usando OCR."""
#
#     # Aumentar o tamanho da imagem para melhorar a precisão do OCR
#     img = np.array(img)
#     img = cv2.resize(img, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
#
#     # Converter para escala de cinza
#     # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#
#     # Aplicar blur para reduzir ruídos
#     # img = cv2.medianBlur(img, 3)
#
#     # Aplicar threshold para converter a imagem em preto e branco
#     # _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#
#     # Salvar a imagem processada, se desejado
#     if salvar_imagem:
#         cv2.imwrite(caminho_salvar, img)
#         print(f"Imagem processada salva em: {caminho_salvar}")
#
#     # Configuração do OCR
#     config_ocr = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
#     texto_extraido = pytesseract.image_to_string(img, config=config_ocr)
#
#     if texto_extraido == None or texto_extraido == '':
#         config_ocr = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
#         texto_extraido = pytesseract.image_to_string(img, config=config_ocr)
#
#     # Remover espaços ou caracteres indesejados
#     texto_limpo = texto_extraido.strip()
#     print('TEXTO PARA NUMERO:' + texto_limpo)
#
#     # Correções manuais
#     texto_limpo = texto_limpo.replace('o', '0').replace('O', '0')
#     if texto_limpo.startswith('7') and len(texto_limpo) > 2:
#         texto_limpo = '2' + texto_limpo[1:]
#
#     try:
#         # Converter para número
#         texto_limpo = int(texto_limpo)
#     except ValueError:
#         print('ERRO AO LER NUMERO: ' + texto_extraido)
#         texto_limpo = None
#
#     return texto_limpo
