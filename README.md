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
python main.py
```

run each ast_[...]
to generate uss

```bash
python ast_to_uss.py
```

uxml
```bash
python ast_to_uxml.py
```

csharp
```bash
python ast_to_csharp.py [ComponentName]
```




