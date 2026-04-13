import re
import json

# pdftohtml -xml -f 192 Dados/ossos.pdf Dados/ossos_anatomia.xml

f = open("ossos_anatomia.xml", "r", encoding="utf8")
texto = f.read()

# Remover declarações do XML e lixo
texto = re.sub(r'<\?xml.*?>|<!DOCTYPE.*?>|</?pdf2xml.*?>', '', texto)
texto = re.sub(r'</?page.*?>|<image.*?>|<fontspec.*?>', '', texto)
texto = re.sub(r'<text[^>]*font="[01234]"[^>]*>.*?</text>', '', texto, flags=re.DOTALL)

# Limpar as tags de formatação visual
texto = re.sub(r'</?b>', '', texto)
texto = re.sub(r'</?i>', '', texto)

# Transformar as tags <text> em quebras de linha limpas
texto = re.sub(r'<text[^>]*>', '', texto)
texto = re.sub(r'</text>', '\n', texto)

# Juntar títulos que o PDF cortou (Ex: "FALANGE E META \n CARPO" -> "FALANGE E META CARPO")
texto = re.sub(r'([A-ZÀ-Ú,])\n\s*([A-ZÀ-Ú:])', r'\1 \2', texto)

# Transformar o texto limpo numa lista de linhas, removendo linhas vazias
linhas = [l.strip() for l in texto.split('\n') if l.strip()]

# ==========================================
# 2. MÁQUINA DE ESTADOS HIERÁRQUICA
# ==========================================
dicionario_final = {}

sistema_atual = None
regiao_atual = None
vista_atual = None

# ==========================================
# AS REGEXES CORRIGIDAS E BLINDADAS
# ==========================================
re_sistema = re.compile(r'^SISTEMA\s+[A-ZÀ-Ú\sE]+$')             # Ex: SISTEMA MUSCULAR
re_regiao = re.compile(r'^\d+\.\s+[A-ZÀ-Ú\s]+$')                 # Ex: 1. CABEÇA E PESCOÇO
# Correção 1: Aceita subsecções "4.4.1" adicionando o (?:\.\d+)?
re_vista = re.compile(r'^\d+\.\s*\d+(?:\.\d+)?\.?\s+[A-ZÀ-Ú].+$') # Ex: 1.1. CRÂNIO ou 4.4.1 VISTA
# Correção 2: Troca de \s+ para \s* para aceitar "e)Corpo" colado
re_item = re.compile(r'^([A-Za-z]\d?)\)\s*(.+)$')                # Ex: a) Osso, e)Corpo, d1) Olho

for l in linhas:
    # Ignorar eventuais restos de cabeçalhos
    if "SUMÁRIO" in l or "AnAtomiA nA práticA" in l or l.isdigit():
        continue

    # --- NÍVEL 0: SISTEMA ---
    if re_sistema.match(l):
        sistema_atual = l
        dicionario_final[sistema_atual] = {}
        regiao_atual = None
        vista_atual = None
        continue

    # --- NÍVEL 1: REGIÃO ---
    if re_regiao.match(l):
        regiao_atual = l
        if sistema_atual:
            if regiao_atual not in dicionario_final[sistema_atual]:
                dicionario_final[sistema_atual][regiao_atual] = {}
        vista_atual = None
        continue

    # --- NÍVEL 2: SUBSECÇÃO / VISTA ---
    if re_vista.match(l):
        vista_atual = l
        if sistema_atual and regiao_atual:
            # Cria a entrada da vista como um dicionário vazio para receber os itens
            dicionario_final[sistema_atual][regiao_atual][vista_atual] = {}
        continue

    # --- NÍVEL 3: ITENS / ALÍNEAS ---
    m_item = re_item.match(l)
    if m_item:
        letra = m_item.group(1)
        nome = m_item.group(2)
        if sistema_atual and regiao_atual and vista_atual:
            # Substituir múltiplos espaços por apenas um
            nome_limpo = re.sub(r'\s+', ' ', nome).strip()
            dicionario_final[sistema_atual][regiao_atual][vista_atual][letra] = nome_limpo
        continue

    # --- RESOLVER TEXTO PARTIDO PELA QUEBRA DE PÁGINA/LINHA ---
    if sistema_atual and regiao_atual and vista_atual:
        itens_da_vista = dicionario_final[sistema_atual][regiao_atual][vista_atual]
        
        # Se a vista atual ainda não tem itens, a linha partida pertence ao nome do Nível 2
        if len(itens_da_vista) == 0:
            novo_nome_vista = vista_atual + " " + l
            dicionario_final[sistema_atual][regiao_atual][novo_nome_vista] = dicionario_final[sistema_atual][regiao_atual].pop(vista_atual)
            vista_atual = novo_nome_vista
            
        # Se já tem itens, a linha partida é o final de uma frase de um Nível 3 (Item)
        else:
            ultima_letra = list(itens_da_vista.keys())[-1]
            dicionario_final[sistema_atual][regiao_atual][vista_atual][ultima_letra] += " " + l.strip()

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("ossos.json", dicionario_final)
