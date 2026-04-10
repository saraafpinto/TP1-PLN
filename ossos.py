import re
import json

f = open("Dados/ossos_anatomia.xml", "r", encoding="utf8")
texto = f.read()

# Remover declarações do XML
texto = re.sub(r'<\?xml.*?>|<!DOCTYPE.*?>|</?pdf2xml.*?>', '', texto)
texto = re.sub(r'</?page.*?>|<image.*?>|<fontspec.*?>', '', texto)

#Remover todo o lixo (Margens, "Sumário", "Gabarito", Números de página)
# Todas essas palavras usam as fontes 0, 1, 2, 3 e 4.
texto = re.sub(r'<text[^>]*font="[01234]"[^>]*>.*?</text>', '', texto)

# Limpar as tags de negrito
texto = re.sub(r'</?b>', '', texto)

# Transformar as tags <text> em quebras de linha limpas
texto = re.sub(r'<text[^>]*>', '', texto)
texto = re.sub(r'</text>', '\n', texto)

# Juntar títulos que o PDF cortou (Ex: "FALANGE E META \n CARPO" -> "FALANGE E META CARPO")
texto = re.sub(r'([A-Z,])\n\s*([A-Z:])', r'\1 \2', texto)


# Procura linhas que comecem por números do tipo "1.1", "1.14." ou "2.1" seguidos de letras Maiúsculas
texto = re.sub(r'^\s*(\d+\.\d+\.?\s+[A-Z].*)', r'\n###\1', texto, flags=re.MULTILINE)


seccoes = re.split(r'\n###', texto)

anatomia_dict = {}

for bloco in seccoes:
    bloco = bloco.strip()
    
    linhas = bloco.split('\n')
    titulo = linhas[0].strip() # A primeira linha é o título da secção (Ex: 1.1 CRÂNIO...)
    
    # Juntar o resto das linhas para procurar os itens
    corpo = "\n".join(linhas[1:])
    
    # Regex para apanhar os Itens: "a) Osso frontal"
    # Grupo 1: Letra (a, b, c1...) | Grupo 2: Nome do osso
    itens = re.findall(r'([a-z]\d?)\)\s*(.+)', corpo)
    
    if itens:
        # Se encontrou itens, cria o dicionário para esta secção
        anatomia_dict[titulo] = {letra: nome.strip() for letra, nome in itens}

def gera_json(filename, dicionario):
    f_out = open(filename, 'w', encoding='utf8')
    json.dump(dicionario, f_out, indent=4, ensure_ascii=False)
    f_out.close()

gera_json("ossos.json", anatomia_dict)
