# BOCA Problem Builder

Repositório com um código simples em python para montar um pacote para o sistema de competição BOCA
Os pacotes gerados nessa branch funcionam corretamente em um Ubuntu Server 22.04 rodando o boca-autojudge sem modificações

## Como usar

### Para gerar um único pacote

```python3 main.py {PROBLEM LETTER} POLYGON_PACKAGE.zip [java_tl_factor] [python_tl_factor]```

Problem Letter é a letra do problema que será gerado, por exemplo, A, B, C, etc.
POLYGON_PACKAGE.zip é o arquivo zipado com o problema do Polygon.
O arquivo zipado do Polygon deve ter sido gerado na opção "Full" e baixado a versão de Linux.
java_tl_factor e python_tl_factor são opcionais e são os fatores de multiplicação do tempo limite de execução para as linguagens Java e Python, respectivamente. O padrão é 1 para ambas.

Por exemplo:
```python3 main.py A POLYGON_PACKAGE.zip```

Após isso, o pacote vai estar na pasta ```packages``` e arquivo zip do pacote para ser importado no BOCA será gerado na pasta ```zip_packages```.

### Para gerar todos pacotes de um contest

```python3 make_contest.py```

As configurações do contest devem ser feitas no arquivo ```config.json```. O arquivo ```config.json.example``` mostra um exemplo de como deve ser feito.

No arquivo ```contest.json``` nas opções de ```POLYGON_PACKAGE``` que estiverem marcadas como ```"DEFAULT"``` (não tiverem caminho especificado), o script vai procurar no diretório ```polygon_packages``` um arquivo zip que começa com a letra do problema. Por exemplo, se o problema for A, o script vai procurar por ```a*.zip```. Se não encontrar, vai procurar por ```*.zip```.

## Como funciona 

// TODO
