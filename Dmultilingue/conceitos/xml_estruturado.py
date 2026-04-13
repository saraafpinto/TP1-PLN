import pdfplumber

def extrair_texto_pdf(pdf_path, txt_path):
    linhas_finais = []

    with pdfplumber.open(pdf_path) as pdf:
        # Extrair das páginas 28 a 181 (onde está o dicionário)
        for i in range(28, 182):
            page = pdf.pages[i]
            mid = page.width / 2.0

            # Coluna Esquerda
            esq_text = page.within_bbox((0, 0, mid, page.height)).extract_text()
            if esq_text: linhas_finais.extend(esq_text.split('\n'))

            # Coluna Direita
            dir_text = page.within_bbox((mid, 0, page.width, page.height)).extract_text()
            if dir_text: linhas_finais.extend(dir_text.split('\n'))

    linhas_limpas = []
    for l in linhas_finais:
        l = l.strip()
        if not l: continue
        # Limpeza pesada de lixo
        if "QUADERNS 50" in l or "DICCIONARI MULTILINGÜE" in l: continue
        if l in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Z", "QUAD", "Diccionari"]: continue
        
        linhas_limpas.append(l)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_limpas))

if __name__ == "__main__":
    extrair_texto_pdf('diccionari-multilinguee-de-la-covid-19.pdf', 'dicionario_bruto.txt')