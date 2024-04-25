# BOCA Problem Builder

Este repositório contém um script Python simples para criar um pacote de problemas para o sistema de competição BOCA. Os pacotes gerados nesta branch funcionam corretamente em um Ubuntu Server 22.04 executando o boca-autojudge sem modificações.

## Como usar

O script recebe um pacote de problema em formato `.zip` gerado pela plataforma Polygon (polygon.codeforces.com). 

Pelo Polygon, na aba `Packages`, gere a versão Full e baixe a opção para Linux.

### Para gerar um único pacote

Execute o seguinte comando:

```python3 main.py PROBLEM_LETTER POLYGON_PACKAGE.zip [java_tl_factor] [python_tl_factor]```

- `PROBLEM_LETTER` é a letra do problema a ser gerado, por exemplo, A, B, C, etc. Deve ser uma letra maiúscula.
- `POLYGON_PACKAGE.zip` é o arquivo zipado com o problema do Polygon. O arquivo zipado do Polygon deve ter sido gerado na opção Full e baixado na versão para Linux.
- `java_tl_factor` e `python_tl_factor` são opcionais e são os fatores de multiplicação do tempo limite de execução para as linguagens Java e Python, respectivamente. O padrão é 1 para ambas.

Por exemplo:
```python3 main.py A POLYGON_PACKAGE.zip```

Após isso, o pacote estará na pasta `packages` e o arquivo zip do pacote para ser importado no BOCA será gerado na pasta `zip_packages`.

### Para gerar todos os pacotes de um contest

Crie um diretório contendo todos os pacotes de problemas a serem utilizados em um contest, e então execute o seguinte comando:

```python3 make_contest.py {CONTEST_DIRECTORY}```

As configurações do contest devem ser feitas no arquivo `CONTEST_DIRECTORY/contest.json`. O arquivo `contest.json.example` mostra um exemplo de como deve ser feito.

No arquivo `contest.json`, nas opções de `POLYGON_PACKAGE` que estiverem marcadas como `DEFAULT` (ou seja, não tiverem um caminho especificado), o script procurará no diretório `CONTEST_DIRECTORY` um arquivo zip que começa com a letra do problema. Por exemplo, se o problema for A, o script procurará por `a*.zip`.

## Sobre o pacote gerado

O pacote gerado é um pacote pronto para ser utilizado no sistema de competições BOCA, testado na versão mais recente do BOCA (1.15.19+), mas deve funcionar na maioria.
As linguagens aceitas para submissão são C, C++, Java, Kotlin e Python 3. O tempo limite de execução para cada problema é o mesmo que o tempo limite de execução do Polygon, multiplicado pelo fator especificado no script. O limite de memória é o mesmo que o do Polygon.
