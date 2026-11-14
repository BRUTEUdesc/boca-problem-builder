# BOCA Problem Builder

Este repositório contém um script Python simples para criar um pacote de problemas para o sistema de competição BOCA. Os pacotes gerados nesta branch funcionam corretamente em um Ubuntu Server 22.04 executando o boca-autojudge sem modificações.

## Como usar

O script recebe um pacote de problema em formato `.zip` gerado pela plataforma [Polygon](https://polygon.codeforces.com). 

Pelo Polygon, na aba `Packages`, gere a opção Full e baixe a opção para Linux.

### Para criar o pacote de um único problema

Execute o seguinte comando:

```python3 make_from_full_package.py PROBLEM_LETTER POLYGON_PACKAGE.zip [java_tl_factor] [python_tl_factor]```

- `PROBLEM_LETTER` é a letra do problema a ser gerado, por exemplo, A, B, C, etc. Deve ser uma letra maiúscula.
- `POLYGON_PACKAGE.zip` é o arquivo zipado com o problema do Polygon. O arquivo zipado do Polygon deve ter sido gerado na opção Full e baixado na versão para Linux.
- `java_tl_factor` e `python_tl_factor` são opcionais e são os fatores de multiplicação do tempo limite de execução para as linguagens Java e Python, respectivamente. O padrão é 1 para ambas.

Por exemplo:
```python3 make_from_full_package.py A aluguel-de-filmes-13$linux.zip```

Após isso, o pacote estará na pasta `packages` e o arquivo zip do pacote para ser importado no BOCA estará na pasta `zip_packages`.

### Para gerar todos os pacotes de um contest

Crie um diretório contendo todos os pacotes de problemas a serem utilizados em um contest, e então execute o seguinte comando:

```python3 make_contest.py /path/to/contest/```

As configurações do contest devem ser feitas no arquivo `/path/to/contest/contest.json`. O arquivo `contest.json.example` mostra um exemplo de como deve ser feito.

No arquivo `contest.json`, nas opções de `POLYGON_PACKAGE` que estiverem marcadas como `DEFAULT` (ou seja, não tiverem um caminho especificado), o script procurará no diretório `/path/to/contest/` um arquivo zip que começa com a letra do problema. Por exemplo, se o problema for A, o script procurará por `a*.zip`.

## Sobre o pacote gerado

O pacote gerado é um pacote pronto para ser utilizado no sistema de competições BOCA, testado na versão mais recente do BOCA (1.15.19+), mas deve funcionar na maioria.
As linguagens aceitas para submissão são C, C++, Java, Kotlin e Python 3. O tempo limite de execução para cada problema é o mesmo que o tempo limite de execução do Polygon, multiplicado pelo fator especificado no script. O limite de memória é o mesmo que o do Polygon.

O checker do Polygon (`check.cpp` com `testlib.h`) é compilado na geração do pacote (`g++ -O2 -std=c++23 -static`) e vai em `compare/check`, para o autojudge não compilar a cada submissão: é preciso rodar o script num Linux x86-64 com `g++` (no Ubuntu, `apt install g++`). Se o checker não compilar, o script para com erro. Problemas com entrada/saída por arquivo não são suportados e são recusados.

Problemas interativos (interactor em C++ com testlib no `problem.xml`) usam `run/` e `compare/` de `problem_template_interactive/`, igual a `src/private/polygontemplate-interactive/` do BOCA. O interactor (`g++ -O2 -std=c++23 -static`) e o launcher `run/interact` (`gcc -O2 -static`, fonte em `run/interact.c`) são compilados na geração e vão no pacote. Para isso é preciso também o `gcc`.

No autojudge, o launcher liga o interactor e a solução por dois pipes diretos, com os dois fixados na mesma CPU:
- o interactor roda fora da jaula, como root, com limites de CPU, memória e arquivo;
- a solução roda sob o safeexec, com os limites de sempre, numa só execução de TL/repetições, e com relógio de 2·TL+2 s.

A entrada não é copiada para a jaula. TLE/RE/MLE da solução valem quando ela terminou antes do interactor. WA/PE do interactor dão Wrong Answer, e FAIL do interactor ou do checker dá "Contact staff". Com o interactor OK, o checker roda sobre a saída (tout) do interactor.

No autojudge, a saída do checker vira: 0 → Accepted; 1 (WA) ou 2 (PE) → Wrong Answer; qualquer outra (3 = FAIL, crash) → "Checker failed", que o BOCA mostra como "Contact staff".
