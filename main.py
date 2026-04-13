import json
import re
import unicodedata
import os

def normalizar_chave(texto):
    """Garante que termos como 'Abdômen' e 'abdome' sejam a mesma chave."""
    if not texto: return ""
    # Remove acentos e converte para minúsculas
    nfkd = unicodedata.normalize('NFKD', str(texto))
    t = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    # Remove marcas de país [Br], classes gramaticais e espaços extras
    t = re.sub(r'\[.*?\]|\s+s\.[mf]\.|\s+n\s+[mf]|\(.*?\)', '', t)
    return t.strip()

def obter_ou_criar_entrada(master, termo_pt):
    """Cria a estrutura base para um novo termo se ele ainda não existir."""
    chave = normalizar_chave(termo_pt)
    if not chave: return None
    
    if chave not in master:
        master[chave] = {
            "termo_principal": termo_pt.split('[')[0].strip(),
            "genero": "",
            "sigla": "",
            "categorias": set(),
            "definicoes": [],
            "inf_encicl": "",
            "traducoes": {},
            "fontes": set()
        }
    return master[chave]

def consolidar_dicionario():
    master = {}

    # --- 1. MEDICINA.JSON (Extração direta pelo termo PT) ---
    if os.path.exists("medicina/medicina.json"):
        with open("medicina/medicina.json", "r", encoding="utf-8") as f:
            dados_med = json.load(f)
            for info in dados_med.values():
                # Vamos buscar o termo português dentro do campo traducoes
                termo_pt_completo = info.get("traducoes", {}).get("pt", "")
                if termo_pt_completo:
                    # Se houver vários sinónimos (separados por ;), processamos todos
                    for termo in termo_pt_completo.split(';'):
                        entry = obter_ou_criar_entrada(master, termo)
                        if entry:
                            entry["fontes"].add("medicina.json")
                            if info.get("genero"): entry["genero"] = info["genero"]
                            if info.get("area"): entry["categorias"].add(info["area"])
                            # Adicionar outras línguas (es, en, la)
                            for lang, trad in info.get("traducoes", {}).items():
                                if lang != "pt":
                                    # Limpa etiquetas como [ing] ou [esp]
                                    limpa = re.sub(r'\s*\[.*?\]', '', str(trad)).strip()
                                    entry["traducoes"][lang] = limpa

    # --- 2. GLOSSÁRIO DE NEOLOGISMOS ---
    if os.path.exists("glossario_neologismos/glossario_neologismos.json"):
        with open("glossario_neologismos/glossario_neologismos.json", "r", encoding="utf-8") as f:
            dados_neo = json.load(f)
            for termo, info in dados_neo.items():
                entry = obter_ou_criar_entrada(master, termo)
                if entry:
                    entry["fontes"].add("glossario_neologismos.json")
                    if info.get("genero"): entry["genero"] = info["genero"]
                    if info.get("sigla"): entry["sigla"] = info["sigla"]
                    if info.get("descricao"): entry["definicoes"].append(info["descricao"])
                    if info.get("inf_encicl"): entry["inf_encicl"] = info["inf_encicl"]
                    # Traduções específicas deste ficheiro
                    trads = info.get("traducao", {})
                    for l, v in trads.items():
                        chave_l = "en" if "ing" in l.lower() else "es" if "esp" in l.lower() else l
                        entry["traducoes"][chave_l] = re.sub(r'\s*\[.*?\]', '', str(v)).strip()

    # --- 3. DICIONÁRIOS COM CHAVE SIMPLES (Termo PT: Info) ---
    fontes_simples = {
        "Glossario_enfermagem/glossario_enfermagem.json": "definicao",
        "glossario_ministerio/conceitos_ministerio.json": "Descricao",
        "glossario_tematico/glossario_tematico_conceitos.json": "definicao",
        "glossario_termos/glossario_termos.json": "significado"
    }

    for ficheiro, campo_def in fontes_simples.items():
        if os.path.exists(ficheiro):
            with open(ficheiro, "r", encoding="utf-8") as f:
                dados = json.load(f)
                for termo, info in dados.items():
                    entry = obter_ou_criar_entrada(master, termo)
                    if entry and isinstance(info, dict):
                        d = info.get(campo_def)
                        if d and d not in entry["definicoes"]:
                            entry["definicoes"].append(d)
                        cat = info.get("Categoria") or info.get("area")
                        if cat: entry["categorias"].add(cat)
                        entry["fontes"].add(ficheiro)

    # --- 4. ESTRUTURAS COMPLEXAS (CIPE e WIPO) ---
    # CIPE (Dicionário de IDs, termo está lá dentro)
    if os.path.exists("ICNP/cipe.json"):
        with open("ICNP/cipe.json", "r", encoding="utf-8") as f:
            for item in json.load(f).values():
                entry = obter_ou_criar_entrada(master, item.get("termo", ""))
                if entry:
                    if item.get("descricao"): entry["definicoes"].append(item["descricao"])
                    if item.get("eixo"): entry["categorias"].add(f"Eixo {item['eixo']}")
                    entry["fontes"].add("cipe.json")

    # WIPO (Chave Inglês, Português dentro de Traduções)
    if os.path.exists("WIPO/wipo.json"):
        with open("WIPO/wipo.json", "r", encoding="utf-8") as f:
            for info in json.load(f).values():
                termo_pt = info.get("Traducoes", {}).get("PT", "")
                if termo_pt:
                    # Limpar variações do tipo "termo, (syn.)"
                    limpo = termo_pt.split(',')[0].strip()
                    entry = obter_ou_criar_entrada(master, limpo)
                    if entry:
                        if info.get("Descricao"): entry["definicoes"].append(info["Descricao"])
                        entry["fontes"].add("wipo.json")

    # --- 5. ORDENAÇÃO E EXPORTAÇÃO ---
    # Ordenar o dicionário alfabeticamente pela chave normalizada
    chaves_ordenadas = sorted(master.keys())
    dicionario_final = {}

    for c in chaves_ordenadas:
        item = master[c]
        # Converter os sets para listas ordenadas para o JSON aceitar
        item["categorias"] = sorted(list(item["categorias"]))
        item["fontes"] = sorted(list(item["fontes"]))
        dicionario_final[c] = item

    with open("DICIONARIO_CONSOLIDADO_FINAL.json", "w", encoding="utf-8") as f_out:
        json.dump(dicionario_final, f_out, indent=4, ensure_ascii=False)

    print(f"Sucesso! {len(dicionario_final)} termos consolidados em ordem alfabética.")

if __name__ == "__main__":
    consolidar_dicionario()