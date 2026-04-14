import json
import re
import unicodedata
import os

def normalizar_chave(texto):
    """Normaliza o termo para comparação (sem acentos, minúsculas)."""
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    t = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    t = re.sub(r'\[.*?\]|\s+s\.[mf]\.|\s+n\s+[mf]|\(.*\)', '', t)
    return t.strip()

def criar_estrutura_base(termo_exibicao):
    """Retorna o template do dicionário com listas para acumulação."""
    return {
        "termo_principal": termo_exibicao,
        "genero": "",
        "siglas": [],
        "categorias": [],
        "definicoes": [],
        "pesquisa": [],
        "inf_encicl": "",
        "sinonimos": [],
        "variantes": [],
        "notas_extras": [],
        "traducoes": {}, 
        "remissoes": [],
        "fontes": []
    }

def limpar_vazios(dicionario):
    """Apaga todas as chaves que estiverem vazias ([], "", {})."""
    if isinstance(dicionario, dict):
        novo_dic = {}
        for k, v in dicionario.items():
            v_limpo = limpar_vazios(v)
            if v_limpo or v_limpo is False or v_limpo == 0: 
                novo_dic[k] = v_limpo
        return novo_dic
    elif isinstance(dicionario, list):
        lista_limpa = [limpar_vazios(item) for item in dicionario]
        return [item for item in lista_limpa if item or item is False or item == 0]
    else:
        return dicionario

def consolidar_final():
    master_dict = {}

    # --- 1. PROCESSAR FICHEIROS PT (Listas e Dicionários de Objetos) ---
    fontes_pt = [
        ("Glossario_enfermagem/glossario_enfermagem.json", "definicao"),
        ("glossario_ministerio/conceitos_ministerio.json", "definicao"),
        ("glossario_neologismos/glossario_neologismos.json", "definição"),
        ("glossario_tematico/glossario_tematico_conceitos.json", "definicao"),
        ("glossario_termos/glossario_termos.json", "definicao"),
        ("ICNP/cipe.json", "definicao"),
        ("ossos/ossos_conceitos.json", "definicao")
    ]

    for filename, field_def in fontes_pt:
        if not os.path.exists(filename): continue
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            # Universalizador: transforma Listas e Dicionários numa lista iterável uniforme
            if isinstance(dados, dict):
                items = dados.items()
            else:
                # Se for lista, o "termo" (a chave principal) está dentro do objeto
                items = [(item.get("termo", ""), item) for item in dados if isinstance(item, dict)]
            
            for termo, info in items:
                chave = normalizar_chave(termo)
                if not chave: continue
                
                if chave not in master_dict:
                    master_dict[chave] = criar_estrutura_base(termo)
                
                ent = master_dict[chave]
                if filename not in ent["fontes"]: ent["fontes"].append(filename)
                
                if isinstance(info, dict):
                    # Acumular definições
                    d = info.get(field_def)
                    if d and d not in ent["definicoes"]: ent["definicoes"].append(d)
                    
                    # Acumular Categorias, Siglas e Género
                    cat = info.get("categoria") or info.get("area") or info.get("eixo")
                    if cat and cat not in ent["categorias"]: ent["categorias"].append(cat)
                    if info.get("sigla") and info["sigla"] not in ent["siglas"]: ent["siglas"].append(info["sigla"])
                    if not ent["genero"] and info.get("genero"): ent["genero"] = info["genero"]
                    
                    # Acumular extras (do Glossário Temático e Neologismos)
                    if info.get("sinonimo") and info["sinonimo"] not in ent["sinonimos"]: ent["sinonimos"].append(info["sinonimo"])
                    
                    # Notas podem vir como lista (temático) ou string
                    notas = info.get("notas") or info.get("nota") or []
                    if isinstance(notas, str): notas = [notas]
                    for n in notas:
                        if n and n not in ent["notas_extras"]: ent["notas_extras"].append(n)
                        
                    # Remissões (temático)
                    remissas = info.get("remissa") or []
                    for r in remissas:
                        if r and r not in ent["remissoes"]: ent["remissoes"].append(r)

                    if info.get("pesquisa") and info["pesquisa"] not in ent["pesquisa"]: ent["pesquisa"].append(info["pesquisa"])

                    # Traduções
                    trads_fonte = info.get("traducoes") or info.get("traducao") or {}
                    if isinstance(trads_fonte, dict):
                        for lang, valor_trad in trads_fonte.items():
                            if not valor_trad: continue
                            
                            # Normalização das chaves das línguas (espanhol -> es, ingles -> en)
                            lang_limpa = lang.lower()
                            if lang_limpa in ["inglês", "ingles", "ing"]: lang_limpa = "en"
                            if lang_limpa in ["espanhol", "esp"]: lang_limpa = "es"
                            
                            if lang_limpa not in ent["traducoes"]: ent["traducoes"][lang_limpa] = []
                            
                            termo_limpo = re.sub(r'\s*\[.*?\]', '', str(valor_trad)).strip()
                            if termo_limpo and termo_limpo not in ent["traducoes"][lang_limpa]:
                                ent["traducoes"][lang_limpa].append(termo_limpo)


    # --- 2. PROCESSAR WIPO E MULTILINGUE (Verificação e Enriquecimento) ---
    fontes_multi = ["WIPO/wipo.json", "Dmultilingue/conceitos/dicionario_conceitos.json"]
    
    for filename in fontes_multi:
        if not os.path.exists(filename): continue
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            # WIPO é um dict, Multilingue é uma list
            lista_iteravel = dados.items() if isinstance(dados, dict) else [(item.get("termo", ""), item) for item in dados if isinstance(item, dict)]
                
            for termo_estrangeiro, info in lista_iteravel:
                trads = info.get("traducoes", {})
                
                # O termo PT pode estar nas traduções, ou ser a própria chave (se for o dicionario_conceitos que tem o termo base em catalão/português)
                pt_term = trads.get("PT") or trads.get("pt [PT]") or info.get("termo")
                
                if pt_term:
                    pt_principal = pt_term.split(',')[0].split(';')[0].strip()
                    chave_pt = normalizar_chave(pt_principal)
                    
                    if chave_pt in master_dict:
                        ent = master_dict[chave_pt]
                        if filename not in ent["fontes"]: ent["fontes"].append(filename)
                        
                        d = info.get("definicao")
                        if d and d not in ent["definicoes"]: ent["definicoes"].append(d)
                        
                        c = info.get("categoria") or info.get("categoria_lexica") or info.get("area_tematica")
                        if c and c not in ent["categorias"]: ent["categorias"].append(c)
                        
                        # Preencher traduções em falta
                        for lang, val in trads.items():
                            if not val: continue
                            l_std = lang.replace(" [PT]", "").replace(" [BR]", "_br").lower()
                            if l_std == "pt": continue 
                            
                            if l_std not in ent["traducoes"]: ent["traducoes"][l_std] = []
                            if val not in ent["traducoes"][l_std]: ent["traducoes"][l_std].append(val)

    # --- 3. LIMPEZA FINAL E ORDENAÇÃO ---
    for chave in master_dict:
        master_dict[chave]["definicoes"] = list(dict.fromkeys(master_dict[chave]["definicoes"]))
        master_dict[chave]["fontes"] = sorted(list(set(master_dict[chave]["fontes"])))
        master_dict[chave]["categorias"] = sorted(list(set(master_dict[chave]["categorias"])))
        master_dict[chave]["siglas"] = sorted(list(set(master_dict[chave]["siglas"])))
        
   
    master_dict_ordenado = dict(sorted(master_dict.items()))

    dicionario_limpo = limpar_vazios(master_dict_ordenado)

    with open('DICIONARIO_GIGANTE_FINAL.json', 'w', encoding='utf-8') as f_out:
        json.dump(dicionario_limpo, f_out, indent=4, ensure_ascii=False)

    print(f"Sucesso! Dicionário consolidado com {len(dicionario_limpo)} termos únicos.")

if __name__ == "__main__":
    consolidar_final()