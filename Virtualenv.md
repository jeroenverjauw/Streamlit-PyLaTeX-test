# Python **virtualenv** Setup

```shell
python -m pip install --upgrade pip
pip install --upgrade virtualenv
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install matplotlib
pip install --upgrade -r requirements-dev.txt
pip install --upgrade -r requirements.txt
# ......
deactivate.bat
```

> Last changed: 2023-02-14
