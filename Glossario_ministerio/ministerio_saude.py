import re, json

# pdftohtml -xml -f 15 -l 106 Dados/glossario_ministerio_saude.pdf Dados/glossario_ministerio.xml

f = open("glossario_ministerio.xml", "r", encoding="utf8")
texto_glos = f.read()

## GLOSSARIO

# Limpezas de tags 
texto_glos = re.sub(r'</?page.*?>|</?pdf2xml.*?>|<image.*?>|<fontspec.*?>', '', texto_glos)
texto_glos = re.sub(r'</?text.*?>', '\n', texto_glos)
texto_glos = re.sub(r'<i>Categoria:\s*</i>', '*\n', texto_glos)
texto_glos = re.sub(r'-\s*\n\s*', '', texto_glos)
texto_glos = re.sub(r'^\s*$', '', texto_glos, flags=re.MULTILINE)
texto_glos = re.sub(r'</?i>', '', texto_glos)

# Se encontrar um </b> seguido de um <b> na linha seguinte, ele apaga as tags e junta o texto
texto_glos = re.sub(r'</b>\s*\n\s*<b>', ' ', texto_glos)

# Findall que para no próximo bold ou no fim do ficheiro
lista_glos = re.findall(r'<b>(.*?)</b>(.*?)(?=<b>|\Z)', texto_glos, re.DOTALL)

# A ALTERAÇÃO: Agora "glossario" é uma lista (Array) em vez de um dicionário!
glossario = [] 

for termo, resto in lista_glos:
    t = termo.strip().replace('\n', ' ')
    conteudo = resto.strip()

    if "*" in conteudo:
        partes = conteudo.split('*', 1)
        linhas = partes[1].strip().split('\n')
        c = linhas[0].strip()
        d = " ".join(linhas[1:]).strip()
    else:
        c = "Sem Categoria"
        d = conteudo.replace('\n', ' ').strip()

    d = re.sub(r'\s+', ' ', d)
    
    # Validar se o termo é real (não deve ser apenas um número de página)
    if not d.isdigit() and len(d) > 3:
        # A ALTERAÇÃO: Fazer o append do objeto criado
        glossario.append({
            "termo": t,
            "categoria": c,
            "definicao": d
        })


## SIGLAS

# pdftohtml -xml -f 5 -l 9 Dados/glossario_ministerio_saude.pdf Dados/siglas.xml

f = open("siglas_ministerio.xml", "r", encoding="utf8")
txt_sig = f.read()
f.close() 

# Limpezas básicas para siglas
txt_sig = re.sub(r"</?page.*?>|<image.*?>|<fontspec.*?>", "", txt_sig)
txt_sig = re.sub(r"</?text.*?>", "\n", txt_sig)
txt_sig = re.sub(r"-\s*\n\s*", "", txt_sig)
txt_sig = re.sub(r'^\s*$', r"", txt_sig, flags=re.MULTILINE)

# apanha o <b> e tudo o que não for tag a seguir ([^<]+)
lista_sig = re.findall(r"<b>(.+?)</b>\s*\n?([^<]+)", txt_sig)

siglas_final = {}

for sigla, significado in lista_sig:
    s = re.sub(r'\s+', ' ', sigla.strip())
    s = re.sub(r"[-–]\s*$", "", s).strip() # Limpa traço no fim
    
    sig = significado.replace("\n", " ").strip()
    sig = re.sub(r'^[-–]\s*', '', sig) # Limpa traço no início
    sig = re.sub(r'\s+', ' ', sig)
    
    if s and len(sig) > 1:
        siglas_final[s] = sig

def gera_json(filename, dicionario):
    f_out= open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False )
    f_out.close()

gera_json("conceitos_ministerio.json", glossario)
gera_json("siglas_ministerio.json", siglas_final)
