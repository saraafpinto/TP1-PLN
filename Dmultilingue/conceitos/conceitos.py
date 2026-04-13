import re
import json

def processar_dicionario(txt_input, json_output):
    f = open(txt_input, "r", encoding="utf8")
    linhas = [l.strip() for l in f.readlines() if l.strip()]

    dicionario = []
    conceito = None
    estado_atual, chave_atual = None, None
    id_gerado = 1
    espera_continuacao = False 
    
    # ==========================================
    # 1. COMPILANDO AS REGEXES PODEROSAS
    # ==========================================
    # Deteta um novo termo separando a palavra da sua categoria gramatical final
    regex_novo_termo = re.compile(r'^(.*?)\s+\b(n m|n f|n m pl|n f pl|n m, f|n m/f|adj|v tr|v tr/intr|v intr|n)$')
    
    # Deteta a linha de uma tradução capturando o idioma e o resto do texto
    regex_idioma = re.compile(r'^(oc|eu|gl|es|en|fr|pt \[PT\]|pt \[BR\]|pt|nl|ar)\s+(.*)')
    
    # Deteta marcadores especiais: CAS, Notas e todos os tipos de Sinónimos
    regex_marcador = re.compile(r'^(CAS|Nota:|sigla|veg\.|sin\.|sin\. compl\.)\s+(.*)')
    
    # Deteta a Área Temática (MAIÚSCULAS) seguida de ponto e a definição
    regex_area_def = re.compile(r'^([A-ZÀ-Ú\s\-]{5,})\.\s*(.*)')
    
    # Deteta pontuação de continuação no fim da linha (; ou ,)
    regex_continuacao = re.compile(r'[;,]$')

    def guardar_pendente(texto):
        texto = texto.strip(" ;")
        if not conceito or not estado_atual or not texto: return
        if estado_atual == 'traducao': conceito["traducoes"][chave_atual] += " " + texto
        elif estado_atual == 'nota': conceito["nota"] += " " + texto
        elif estado_atual == 'cas': conceito["CAS"] += " " + texto
        elif estado_atual == 'sinonimo': conceito["sinonimos"][-1] += " " + texto
        elif estado_atual == 'definicao': conceito["definicao"] += " " + texto

    # ==========================================
    # 2. MOTOR DE LEITURA
    # ==========================================
    for linha in linhas:
        # Netejar os números que o PDF pôs no início (ex: "5 DNA n m" -> "DNA n m")
        linha = re.sub(r'^\d+\s+', '', linha)
        linha = re.sub(r';\s*\d+$', ';', linha) # Tira números após um ponto e vírgula
        
        if not linha or linha.isdigit(): continue

        # FORÇAR A CONTINUAÇÃO: se a anterior acabou com ";" ou ","
        if espera_continuacao:
            guardar_pendente(linha)
            espera_continuacao = bool(regex_continuacao.search(linha))
            continue

        tem_marcador = False
        
        # === A MAGIA DO REGEX: Disparamos todos os detetores! ===
        m_idioma = regex_idioma.match(linha)
        m_marcador = regex_marcador.match(linha)
        m_area_def = regex_area_def.match(linha)
        m_termo = regex_novo_termo.match(linha)

        # 1. É UM IDIOMA?
        if m_idioma:
            tem_marcador = True
            if conceito:
                estado_atual = 'traducao'
                chave_atual = m_idioma.group(1).strip()
                conceito["traducoes"][chave_atual] = m_idioma.group(2).strip(" ;")
                
        # 2. É UM MARCADOR (CAS, Nota, Sinónimo)?
        elif m_marcador:
            tem_marcador = True
            if conceito:
                tipo = m_marcador.group(1).strip()
                resto = m_marcador.group(2).strip(" ;")
                
                if tipo == "CAS":
                    estado_atual, conceito["CAS"] = 'cas', resto
                elif tipo == "Nota:":
                    estado_atual, conceito["nota"] = 'nota', resto
                else: # É um Sinónimo/Sigla
                    estado_atual = 'sinonimo'
                    conceito["sinonimos"].append(f"{tipo} {resto}")
                    
        # 3. É UMA ÁREA TEMÁTICA / DEFINIÇÃO?
        elif m_area_def:
            tem_marcador = True
            if conceito:
                estado_atual = 'definicao'
                conceito["area_tematica"] = m_area_def.group(1).strip()
                conceito["definicao"] = m_area_def.group(2).strip()

        # 4. É UM CONCEITO NOVO?
        elif m_termo and ';' not in linha:
            if conceito: dicionario.append(conceito)
            conceito = {
                "id": id_gerado,
                "termo": m_termo.group(1).strip(),
                "categoria": m_termo.group(2).strip(),
                "traducoes": {}, "sinonimos": [], "CAS": "", "area_tematica": "", "definicao": "", "nota": ""
            }
            id_gerado += 1
            estado_atual = None
            espera_continuacao = False
            continue # Avança para a próxima linha

        # 5. É CONTINUAÇÃO DE TEXTO? (Nenhum Regex de marcação bateu certo)
        if not tem_marcador and not m_termo:
            guardar_pendente(linha)
            
        # Atualiza a flag de continuação usando o regex
        espera_continuacao = bool(regex_continuacao.search(linha))

    # Guardar o último conceito que ficou em memória
    if conceito: dicionario.append(conceito)

    
    f_out = open(json_output, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()
        

if __name__ == "__main__":
    processar_dicionario('dicionario_bruto.txt', 'dicionario_conceitos.json')