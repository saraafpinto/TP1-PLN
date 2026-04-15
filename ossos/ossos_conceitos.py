import re
import json

# pdftotext -raw -f 11 -l 180 Dados/ossos.pdf ossos/ossos_conceitos.txt

f = open("ossos_conceitos.txt", "r", encoding="utf8")
texto = f.read()
f.close()


# Limpar as tags do xml, cabeçalhos e rodapés
texto = re.sub(r'A\s*natomia\s*na\s*prática\s*:\s*S\s*istema\s*M\s*usculoesquelético', ' ', texto, flags=re.IGNORECASE)
texto = re.sub(r'^SUMÁRIO$', ' ', texto, flags=re.MULTILINE)
texto = re.sub(r'^\d+$', ' ', texto, flags=re.MULTILINE) # Números de página 
texto = re.sub(r'^SISTEMA\s+[A-ZÀ-Ú\sE]+$', ' ', texto, flags=re.MULTILINE) # Ex: SISTEMA ESQUELÉTICO


# Padrão: 
# 1.Captura o número e o NOME (ex: "CRÂNIO"), 
# 2.Captura tudo no meio (a definição)
# 3.Para quando encontrar a próxima secção principal (ex: 2.1) ou o fim do ficheiro (\Z)
padrao_extracao = re.compile(r'^\s*(\d+)\.\s+([A-ZÀ-Ú\s]+)\n(.*?)(?=^\s*\d+\.\d+|\Z)', re.MULTILINE | re.DOTALL)

blocos_extraidos = padrao_extracao.findall(texto)

lista_final = []

for numero, termo_bruto, definicao_bruta in blocos_extraidos:
    
    termo = termo_bruto.strip()

    definicao = re.split(r'\n\s*\d+\.\s*\d+\.\s*[A-ZÀ-Ú]', definicao_bruta)[0]
    
    # Remover a palavra "Introdução" do início da definição
    definicao = re.sub(r'^\s*Introdução\s*', '', definicao, flags=re.IGNORECASE)
    
    # Substituir os \n por espaços
    definicao = re.sub(r'\s+', ' ', definicao).strip()
    
    if termo and definicao:
        lista_final.append({
            "termo": termo,
            "definicao": definicao
        })

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("ossos_conceitos.json", lista_final)



