# BOCA Problem Builder

Este repositório contém um script Python simples para criar um pacote de problemas para o sistema de competição BOCA. Os pacotes gerados nesta branch funcionam corretamente em um Ubuntu Server 22.04 executando o boca-autojudge sem modificações.

## Como usar

### Para gerar um único pacote

Execute o seguinte comando:

```python3 main.py {PROBLEM_LETTER} POLYGON_PACKAGE.zip [java_tl_factor] [python_tl_factor]```

- `PROBLEM_LETTER` é a letra do problema a ser gerado, por exemplo, A, B, C, etc.
- `POLYGON_PACKAGE.zip` é o arquivo zipado com o problema do Polygon. O arquivo zipado do Polygon deve ter sido gerado na opção "Full" e a versão Linux deve ter sido baixada.
- `java_tl_factor` e `python_tl_factor` são opcionais e são os fatores de multiplicação do tempo limite de execução para as linguagens Java e Python, respectivamente. O padrão é 1 para ambas.

Por exemplo:
```python3 main.py A POLYGON_PACKAGE.zip```

Após isso, o pacote estará na pasta `packages` e o arquivo zip do pacote para ser importado no BOCA será gerado na pasta `zip_packages`.

### Para gerar todos os pacotes de um contest

Execute o seguinte comando:

```python3 make_contest.py {CONTEST_DIRECTORY}```

As configurações do contest devem ser feitas no arquivo `CONTEST_DIRECTORY/contest.json`. O arquivo `contest.json.example` mostra um exemplo de como deve ser feito.

No arquivo `contest.json`, nas opções de `POLYGON_PACKAGE` que estiverem marcadas como `DEFAULT` (ou seja, não tiverem um caminho especificado), o script procurará no diretório `CONTEST_DIRECTORY` um arquivo zip que começa com a letra do problema. Por exemplo, se o problema for A, o script procurará por `a*.zip`.

## Como funciona 

// TODO
