# ui-transformer

set up

1. create env

```bash
python -m venv venv
```

2. then activate virtual env
```bash
source ./venv/Scripts/activate
```

3. then install dependencies
```bash
pip install -r ./requirements.txt
```

run main to create AST for component

```bash
python docs_to_json_ast.py [ComponentName]
```

run each ast_[...]
to generate uss

```bash
python ast_to_uss.py [ComponentName]
```

uxml
```bash
python ast_to_uxml.py [ComponentName]
```

csharp
```bash
python ast_to_csharp.py [ComponentName]
```




