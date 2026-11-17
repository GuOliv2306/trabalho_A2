"""
Livros de códigos da análise de conteúdo (Bardin).

Cada corpus tem unidade de registro, regra de enumeração e variáveis. Cada variável tem
categorias mutuamente exclusivas (a primeira regra que casa vence, na ordem listada) e
exaustivas (`padrao` é a categoria residual). Tudo é dado puro: a API publica o livro, o
codificador por regras o executa e o codificador por IA o recebe como instrução.

Tipos de regra de uma categoria:
- "regex": lista de expressões (sem diferenciar maiúsculas) testadas no campo da variável;
- "faixa": [mínimo, máximo) para campo numérico;
- variável com "maior_area": True lê 'formato:área|formato:área' e fica com o de maior área;
- "primeira_no_texto": entre as categorias listadas vale a que aparece primeiro no texto.

O casamento ignora maiúsculas e acentos ("promocao" casa com r"promoç").

"regras_de_decisao" são as instruções para casos duvidosos: valem para qualquer codificador
(regras, IA ou pessoa) e nasceram dos desacordos da primeira rodada de validação.
"""

MARCAS = ["trilhamax", "corremais", "campobase"]

CODEBOOKS = {
    "seo_consultas": {
        "versao": 2,
        "titulo": "Consultas de busca",
        "unidade_de_registro": "a consulta digitada no buscador",
        "regra_de_enumeracao": "presença: cada consulta recebe um código por variável; frequências ponderáveis por impressões",
        "variaveis": {
            "intencao": {
                "definicao": "O que a pessoa quer fazer, segundo o que está escrito na consulta.",
                "campo": "text",
                "padrao": "indefinida",
                "regras_de_decisao": [
                    "Nome de marca, sozinho ou acompanhado, é navegacional.",
                    "Palavras de preço e compra (preço, barato, promoção, frete, onde comprar) são transacionais.",
                    "Pergunta em forma de 'como', 'o que', 'para que' é informacional, mesmo sobre escolher produto.",
                ],
                "categorias": [
                    {"codigo": "navegacional", "definicao": "Quer chegar a um site ou marca específica.",
                     "exemplos": ["trilhamax login", "loja corremais"],
                     "regex": [r"\b(" + "|".join(MARCAS) + r")\b", r"\bsite oficial\b", r"\blogin\b"]},
                    {"codigo": "informacional", "definicao": "Quer aprender ou entender algo.",
                     "exemplos": ["como escolher barraca de camping", "o que é garrafa térmica"],
                     "regex": [r"\bcomo\b", r"\bo que\b", r"\bpara que\b", r"\bpor ?que\b", r"\bdicas?\b", r"\bguia\b"]},
                    {"codigo": "transacional", "definicao": "Quer comprar ou fechar negócio agora.",
                     "exemplos": ["comprar tênis de corrida", "mochila de trilha preço"],
                     "regex": [r"\bcomprar\b", r"\bpreços?\b", r"\bpromoç", r"\bfrete\b", r"\bbarat[oa]s?\b",
                               r"\bdescontos?\b", r"\bcupom\b"]},
                    {"codigo": "comercial", "definicao": "Está comparando opções antes de decidir a compra.",
                     "exemplos": ["melhor fone bluetooth", "bota de trekking vale a pena"],
                     "regex": [r"\bmelhor(es)?\b", r"\bvale a pena\b", r"\bavaliaç", r"\btop \d+\b", r"\bou\b",
                               r"\bvs\b", r"\bcompara"]},
                    {"codigo": "indefinida", "definicao": "O texto da consulta não revela a intenção (ex.: só o nome do produto).",
                     "exemplos": ["lanterna de cabeça"]},
                ],
            },
            "formato_serp": {
                "definicao": "Formato que ocupa a maior área da página de resultados. É um registro da plataforma, não uma interpretação.",
                "campo": "serp_features",
                "padrao": "links_organicos",
                "maior_area": True,
                "regras_de_decisao": ["Em caso de empate de área, vale o formato listado primeiro."],
                "categorias": [
                    {"codigo": "links_organicos", "definicao": "Lista tradicional de links."},
                    {"codigo": "snippet_em_destaque", "definicao": "Resposta pronta no topo da página."},
                    {"codigo": "shopping", "definicao": "Vitrine de produtos com preço."},
                    {"codigo": "video", "definicao": "Carrossel de vídeos."},
                    {"codigo": "pacote_local", "definicao": "Mapa com estabelecimentos."},
                    {"codigo": "sitelinks", "definicao": "Links internos de um mesmo site."},
                ],
            },
        },
    },
    "seo_paginas": {
        "versao": 2,
        "titulo": "Páginas do site",
        "unidade_de_registro": "a página (URL), com título, tamanho do texto e assinatura",
        "regra_de_enumeracao": "presença: cada página recebe um código por variável",
        "variaveis": {
            "tipo_pagina": {
                "definicao": "Função da página no site, lida no endereço.",
                "campo": "unit_id",
                "padrao": "institucional",
                "categorias": [
                    {"codigo": "home", "definicao": "Página inicial.", "regex": [r"^https?://[^/]+/?$"]},
                    {"codigo": "produto", "definicao": "Página de um produto.", "regex": [r"/produtos/item-"]},
                    {"codigo": "categoria", "definicao": "Lista de produtos de uma categoria.", "regex": [r"/produtos/categoria-"]},
                    {"codigo": "post", "definicao": "Artigo de blog.", "regex": [r"/blog/"]},
                    {"codigo": "institucional", "definicao": "Sobre, contato, políticas e similares."},
                ],
            },
            "profundidade": {
                "definicao": "Extensão do texto principal, em palavras.",
                "campo": "word_count",
                "padrao": "rasa",
                "categorias": [
                    {"codigo": "rasa", "definicao": "Menos de 300 palavras.", "faixa": [0, 300]},
                    {"codigo": "media", "definicao": "De 300 a 1.199 palavras.", "faixa": [300, 1200]},
                    {"codigo": "profunda", "definicao": "1.200 palavras ou mais.", "faixa": [1200, None]},
                ],
            },
            "autoria": {
                "definicao": "Sinais de autoria e experiência na assinatura da página.",
                "campo": "byline",
                "padrao": "sem_autoria",
                "regras_de_decisao": [
                    "Revisão por especialista conta como credencial, mesmo que o especialista não seja nomeado.",
                    "Assinatura coletiva (equipe, redação) é sem_autoria.",
                ],
                "categorias": [
                    {"codigo": "sem_autoria", "definicao": "Sem assinatura, ou assinatura coletiva que não identifica ninguém.",
                     "exemplos": ["", "Equipe Editorial", "Redação"],
                     "regex": [r"^\W*$", r"^\s*n/?a\s*$", r"\bequipe\b", r"\bredação\b"]},
                    {"codigo": "autor_com_credenciais",
                     "definicao": "Pessoa nomeada com formação, cargo, revisão por especialista ou experiência de uso declarada.",
                     "exemplos": ["Por Ana Lima, fisioterapeuta com 10 anos de experiência"],
                     "regex": [r"experiência", r"especialista", r"certificad", r"revisado por", r"\btestou\b", r"\bdr\.?a?\b"]},
                    {"codigo": "autor_identificado", "definicao": "Pessoa nomeada, sem credenciais.",
                     "exemplos": ["Por Bruno Reis"], "regex": [r"[a-z]{2,}"]},
                ],
            },
        },
    },
    "wikipedia_resumos": {
        "versao": 2,
        "titulo": "Resumos de edição da Wikipedia",
        "unidade_de_registro": "o resumo de edição (campo opcional que acompanha cada revisão)",
        "regra_de_enumeracao": "presença: cada revisão recebe um código por variável",
        "variaveis": {
            "tipo_edicao": {
                "definicao": "O que a edição declara fazer. O nome da seção (/* ... */) não conta: é inserido pelo software.",
                "campo": "text",
                "remover": r"/\*(?!\s*growthexperiments).*?\*/",
                "padrao": "sem_informacao",
                "primeira_no_texto": ["fontes", "forma", "conteudo"],
                "regras_de_decisao": [
                    "Resumo com várias ações: vale a primeira declarada.",
                    "Só é reversão o que se declara como desfazer ou reverter. Remoção feita à mão, com justificativa, é conteudo.",
                    "Inserir, trocar ou remover imagem é conteudo.",
                    "Marcador automático de ferramenta (ex.: growthexperiments, correções semiautomáticas) é manutencao_assistida.",
                    "Promessa, agradecimento ou comentário que não descreve a edição é sem_informacao.",
                ],
                "categorias": [
                    {"codigo": "reversao", "definicao": "Desfaz edição de outra pessoa.",
                     "exemplos": ["Desfeita a edição 123 de X", "Foram revertidas as edições de X"],
                     "regex": [r"\bdesfeit", r"\bdesfiz", r"\brevert", r"\breversão\b", r"\brv\b", r"\bdesfaz"]},
                    {"codigo": "administrativa", "definicao": "Ação de administração: proteger, mover, ocultar.",
                     "exemplos": ["Protegeu \"ChatGPT\": alterações indevidas"],
                     "regex": [r"^\s*(des)?protegeu\b", r"\bmoveu \[\[", r"\bocult(ou|ad)"]},
                    {"codigo": "manutencao_assistida", "definicao": "Manutenção feita por robô ou ferramenta semiautomática.",
                     "exemplos": ["robô: Arquivamento de 14 URLs", "adicionou [[Categoria:X]] usando HotCat"],
                     "regex": [r"\b(bot|robô)(\]\])?\s*:", r"iabot", r"\barquivamento de \d+", r"\busando \[\[",
                               r"\butilizando \[\[", r"\bawb\b", r"growthexperiments", r"semiautom"]},
                    {"codigo": "fontes", "definicao": "Acrescenta, corrige ou remove fontes e referências.",
                     "exemplos": ["inserindo referência sobre o estudo"],
                     "regex": [r"\bfontes?\b", r"ref[eê]r?[eê]nc", r"\brefs?\b", r"\bcitaç", r"\bcitar\b", r"bibliograf",
                               # verbo genérico seguido de perto pelo objeto "referência": a ação é sobre fontes
                               r"\b(inser|adi[cç]|acresc|inclu|coloc|remo[vç]|retir|corr)\w*\s+(\w+\s+){0,2}(ref[eê]r?[eê]nc|fontes?\b|refs?\b|citaç)"]},
                    {"codigo": "forma", "definicao": "Ajuste de forma: ortografia, formatação, links, categorias, tradução de termos.",
                     "exemplos": ["Corrigiu erro ortográfico", "hiperligações"],
                     "regex": [r"ortogr", r"gramát", r"\btypos?\b", r"formata", r"pontua", r"\bcorr(e[cç]|ig)", r"\bajust",
                               r"\bestilo\b", r"ligaç", r"\blink", r"categoria", r"wikific", r"clean ?up", r"\bgrafia\b",
                               r"\bnegrito\b", r"\bitálico\b", r"maiúscul", r"minúscul", r"idiomátic", r"\breorganiz",
                               r"\brecoloc", r"\bredaç"]},
                    {"codigo": "conteudo", "definicao": "Acrescenta, atualiza ou remove informação do artigo, inclusive imagens.",
                     "exemplos": ["Adição de conteúdo", "atualizei os dados de 2024"],
                     "regex": [r"\badi[cç]", r"\bacresc", r"\binser", r"\binclu", r"\bexpan", r"\batualiz", r"\bcriad",
                               r"\btradu", r"\bremo[vç]", r"\bretir", r"\bsubstitu", r"\bincorpor", r"\bmelhori",
                               r"\bconteúdo\b", r"\bexemplo", r"\binforma", r"\bdados\b", r"\btexto\b",
                               r"\bimage[mn]", r"\bfotos?\b", r"^\s*nova página"]},
                    {"codigo": "sem_informacao", "definicao": "Resumo em branco, só com o nome da seção, ou que não descreve a edição.",
                     "exemplos": ["", "/* História */", "muito obrigado", "depois eu adiciono fontes"],
                     # promessa e agradecimento não descrevem a edição (regra de decisão 5)
                     "regex": [r"^\s*(muito\s+)?obrigad", r"\b(depois|vou|irei)\b.{0,20}\b(adicion|inser|coloc)"]},
                ],
            },
            "origem_do_resumo": {
                "definicao": "Quem escreveu o texto do resumo: a pessoa ou o software.",
                "campo": "text",
                "padrao": "escrito_pelo_editor",
                "regras_de_decisao": [
                    "Texto de ferramenta com justificativa digitada junto (ex.: 'Desfeita a edição 1 de X: spam') é gerado_pelo_software.",
                    "Só o nome da seção entre /* */ é gerado_pelo_software.",
                ],
                "categorias": [
                    {"codigo": "em_branco", "definicao": "Nenhum texto.", "regex": [r"^\s*$"]},
                    {"codigo": "gerado_pelo_software",
                     "definicao": "Texto produzido por botão, ferramenta ou robô (desfazer, reverter, HotCat, só o nome da seção).",
                     "exemplos": ["/* História */", "Desfeita a edição 123 de X"],
                     "regex": [r"^\s*(/\*((?!\*/).)*\*/\s*)+$", r"\bdesfeita", r"^\s*(foram|foi) \[\[",
                               r"\b(bot|robô)(\]\])?\s*:", r"iabot",
                               r"\busando \[\[", r"\butilizando \[\[", r"^\s*(des)?protegeu\b", r"growthexperiments",
                               r"\bmoveu \[\[", r"semiautom", r"^\s*nova página:", r"\barquivamento de \d+"]},
                    {"codigo": "escrito_pelo_editor", "definicao": "Texto livre digitado por quem editou."},
                ],
            },
        },
    },
}

LEITURA_DO_MEIO = {
    "seo_consultas": [
        "A intenção é inferida só do texto da consulta: 'indefinida' não é falha do método, é o limite do que o registro mostra.",
        "O buscador só entrega as consultas que decidiu exibir e associar ao site; consultas raras são omitidas.",
        "O formato da página de resultados é decisão da plataforma e muda o CTR sem que a página mude.",
        "Atenção: consultas e formatos são sintéticos (simulador). Os textos saem de moldes, então a concordância com `verdade_simulador` é otimista.",
    ],
    "seo_paginas": [
        "Tipo de página é lido no endereço e profundidade na contagem de palavras: são proxies de template e de extensão, não de qualidade.",
        "Sinais de autoria são o que a página declara; a análise não verifica se a credencial é verdadeira.",
        "Atenção: páginas sintéticas (simulador). A concordância com `verdade_simulador` é otimista.",
    ],
    "wikipedia_resumos": [
        "O resumo é opcional e autodeclarado: descreve o que quem editou diz ter feito, não o que a edição fez.",
        "Boa parte do texto não foi escrita por pessoas: desfazer, reverter, HotCat e o nome da seção são preenchidos pelo software (veja origem_do_resumo).",
        "Resumo em branco não é 'sem motivo': é a interface permitindo salvar sem explicar.",
        "A referência usada na validação foi codificada por IA, não por humanos: mede consistência entre dois procedimentos, não validade.",
    ],
}
