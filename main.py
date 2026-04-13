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
        "traducoes": {
            "en": "", "es": "", "fr": "", "la": "", "it": "",
            "AR": "", "DE": "", "JA": "", "KO": "", "RU": "", "ZH": "",
            "oc": "", "eu": "", "gl": "", "nl": "", "ar": ""
        },
        "remissoes": [],
        "fontes": []
    }

def consolidar_final():
    master_dict = {}

    # --- 1. PROCESSAR FICHEIROS PORTUGUESES PRIMEIRO (Âncoras) ---
    # Estes ficheiros definem o que "já existe" no dicionário
    fontes_pt = [
        ("medicina/medicina.json", "definicao"), 
        ("Glossario_enfermagem/glossario_enfermagem.json", "definicao"),
        ("glossario_ministerio/conceitos_ministerio.json", "Descricao"),
        ("glossario_medico/glossario_medico.json", "definicao"),
        ("glossario_neologismos/glossario_neologismos.json", "definição"),
        ("glossario_tematico/glossario_tematico_conceitos.json", "definicao"),
        ("glossario_termos/glossario_termos.json", "definicao"),
        ("ICNP/cipe.json", "definicao"),
        ("ossos/ossos.json", "definicao")
    ]

    for filename, field_def in fontes_pt:
        if not os.path.exists(filename): continue
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            items = dados if isinstance(dados, list) else dados.items()
            
            for item in items:
                if isinstance(item, tuple): termo, info = item
                else: termo, info = item.get("termo", ""), item
                
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
                    
                    # Acumular Categorias/Eixos
                    cat = info.get("categoria") or info.get("area") or info.get("eixo")
                    if cat and cat not in ent["categorias"]: ent["categorias"].append(cat)
                    
                    # Siglas e Género
                    if info.get("sigla") and info["sigla"] not in ent["siglas"]: ent["siglas"].append(info["sigla"])
                    if not ent["genero"] and info.get("genero"): ent["genero"] = info["genero"]
                    
                    # Notas e Pesquisa
                    if info.get("nota") and info["nota"] not in ent["notas_extras"]: ent["notas_extras"].append(info["nota"])
                    if info.get("pesquisa") and info["pesquisa"] not in ent["pesquisa"]: ent["pesquisa"].append(info["pesquisa"])

                    # Lista de línguas que queres monitorizar
                    linguas = ["en", "es", "fr", "la", "it", "AR", "DE", "JA", "KO", "RU", "ZH", "oc", "eu", "gl", "nl", "ar"]

                    # Obtemos o dicionário de traduções do ficheiro atual (se existir)
                    trads_fonte = info.get("traducoes") or info.get("Traducoes") or info.get("traducao") or {}

                    if isinstance(trads_fonte, dict):
                        for l in linguas:
                            # Procuramos a tradução para a língua 'l' no ficheiro atual
                            # Tentamos a chave em minúsculas e maiúsculas (ex: 'en' e 'EN')
                            valor_trad = trads_fonte.get(l) or trads_fonte.get(l.upper())
                            
                            if valor_trad:
                                # Se a língua ainda não for uma lista no dicionário mestre, inicializamos
                                if not isinstance(ent["traducoes"].get(l), list):
                                    ent["traducoes"][l] = []
                                
                                # Limpamos o termo (removendo [ing], [esp], etc.)
                                termo_limpo = re.sub(r'\s*\[.*?\]', '', str(valor_trad)).strip()
                                
                                # Adicionamos à lista se ainda não lá estiver
                                if termo_limpo and termo_limpo not in ent["traducoes"][l]:
                                    ent["traducoes"][l].append(termo_limpo)

    # --- 2. PROCESSAR WIPO E MULTILINGUE (Verificação e Enriquecimento) ---
    # Só adiciona informação se o termo PT já existir no dicionário
    fontes_multi = ["wipo.json", "multilingue.json"]
    
    for filename in fontes_multi:
        if not os.path.exists(filename): continue
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            for foreign_term, info in dados.items():
                trads = info.get("traducoes", info.get("Traducoes", {}))
                pt_term = trads.get("pt") or trads.get("PT") or trads.get("pt [PT]")
                
                if pt_term:
                    # Limpar para encontrar a chave (ex: "SIDA; AIDS" -> "sida")
                    pt_principal = pt_term.split(',')[0].split(';')[0].strip()
                    chave_pt = normalizar_chave(pt_principal)
                    
                    if chave_pt in master_dict:
                        ent = master_dict[chave_pt]
                        if filename not in ent["fontes"]: ent["fontes"].append(filename)
                        
                        # Acumular definições estrangeiras
                        d = info.get("definicao") or info.get("Definicao")
                        if d and d not in ent["definicoes"]: ent["definicoes"].append(d)
                        
                        # Preencher traduções em falta
                        for lang, val in trads.items():
                            l_std = lang.replace(" [PT]", "").replace(" [BR]", "").lower()
                            if l_std in ent["traducoes"] and not ent["traducoes"][l_std]:
                                ent["traducoes"][l_std] = val
                            elif lang in ent["traducoes"] and not ent["traducoes"][lang]:
                                ent["traducoes"][lang] = val

    # --- 3. LIMPEZA FINAL ---
    # Removemos duplicados exatos dentro das listas e ordenamos
    for chave in master_dict:
        # Usamos dict.fromkeys para remover duplicados mantendo a ordem original
        master_dict[chave]["definicoes"] = list(dict.fromkeys(master_dict[chave]["definicoes"]))
        master_dict[chave]["fontes"] = sorted(list(set(master_dict[chave]["fontes"])))
        master_dict[chave]["categorias"] = sorted(list(set(master_dict[chave]["categorias"])))
        master_dict[chave]["siglas"] = sorted(list(set(master_dict[chave]["siglas"])))

    with open('DICIONARIO_GIGANTE_FINAL.json', 'w', encoding='utf-8') as f_out:
        json.dump(master_dict, f_out, indent=4, ensure_ascii=False)

    print(f"Sucesso! Dicionário consolidado com {len(master_dict)} termos únicos.")

if __name__ == "__main__":
    consolidar_final()