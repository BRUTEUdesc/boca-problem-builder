# BOCA Problem Builder

Repositório com um código simples em python para montar um pacote para o sistema de competição BOCA
Os pacotes gerados nessa branch funcionam corretamente em um Ubuntu Server 22.04 rodando o boca-autojudge sem modificações

## Como usar

```Usage: python3 main.py {PROBLEM LETTER} POLYGON_PACKAGE.zip```

Problem Letter é a letra do problema que será gerado, por exemplo, A, B, C, etc.
POLYGON_PACKAGE.zip é o arquivo zipado com o problema do Polygon.
O arquivo zipado do Polygon deve ter sido gerado na opção "Full" e baixado a versão de Linux.

Por exemplo:
```python3 main.py A POLYGON_PACKAGE.zip```

Após isso, o arquivo zip do pacote para ser importado no BOCA será gerado na pasta ```zip_packages```.

## Como funciona 

// TODO
