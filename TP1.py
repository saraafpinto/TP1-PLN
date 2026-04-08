import re

#ler ficheiro txt

f = open("Dados/medicina.txt", "r", encoding="utf8") #se der problemas por 
texto = f.read()

# Retirar a contagem das paginas
texto = re.sub(r'\n{2,}\d+\n{2,}', '\n\n', texto)
texto = re.sub(r'\s+Índice de denominacións latinas\s+', '\n', texto)

# por o numero dos conceitos direitos
texto = re.sub(r'\n\d+', '', texto)

#juntar os conceitos por letras
texto = re.sub(r'\d\n\n([a-z])', r'\n\1', texto)

#juntar a designacao toda numa linha
texto = re.sub(r'([a-z])\n([a-z])', r'\1 \2', texto)

conceitos = re.split(r"\n^(?=[a-z])", texto, flags=re.MULTILINE)

#print(texto)
#print(conceitos)
conceitos_dict = {}
for c in conceitos[1:]:
    elems = re.split(r",", c, maxsplit=1)
    if len(elems)>1:
        designacao = elems[0]
        numero = elems[1]
        conceitos_dict[designacao] = numero
    else:
        print(f"DEBUG: O item '{c}' não tem vírgula!")
        continue

#print(conceitos_dict)

def gera_html(filename, conceitos_dict):
    html = """
    <html>
        <head>
        <title> Dicionário Médico </title>
        <meta charset="UTF-8">
        </head>
        <body>"""

    for c in conceitos_dict:
        html = html + f"""
        <div>
            <p> <b> {c} </b> </p>
            <p> {conceitos_dict[c]} </p>
        </div>
        <hr>
        """
    html = html + """</body>
    </html>
    """   

    f_out = open(filename, "w", encoding="utf8")
    f_out.write(html)

gera_html("medicina.html", conceitos_dict)