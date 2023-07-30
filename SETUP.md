# Canada Visa From Extraction

## 1 Installation

### 1.1 Manually

**tip:** You can use `mamba` to hugely speed up the installation process. If you don't want to, replace all instances of the `mamba` with `conda` in following steps.

#### 1.1.1 Create a `conda` env

Well all packages gonna be here.
>`conda create --name cvfe python=3.11.0 -y`

#### 1.1.2 Activate the new environment

Make sure you activate this environment right away:
>`conda activate cvfe`

#### 1.1.3 Update `pip`

You should have at least `pip >= 23.1.2`
>`pip install --upgrade pip`

#### 1.1.4 Pin the Python version

When using `conda`, `mamba` and so on, it might update the Python to its latest version. We should prevent that by pinning the Python version in the `conda` environment. To do so:

`echo "python 3.11.0" >>$CONDA_PREFIX/conda-meta/pinned`

#### 1.1.5 Install Processing Dependencies

We need `pandas` and `numpy` and some others, but installing `pandas` will install all those needed.

> `mamba install pandas`

#### 1.1.5 Install data extraction dependencies

>1. `mamba install -c conda-forge xmltodict>=0.13.0 -y`
>2. `pip install pikepdf>=5.1.5`
>3. `pip install pypdf2>=2.2.1`

#### 1.1.6 Install API libs

These libraries (the main one is FastAPI) are not for the ML part and only are here to provide the API and web services.

>1. `pip install pydantic>=1.9.1`
>2. `pip install fastapi>=0.85.0`
>3. `pip install gunicorn>=20.1.0`
>4. `pip install uvicorn>=0.18.2`
>5. `pip install python-multipart>=0.0.5`

*\[Optional\]* For making it online using `ngrok`:

1. `pip install pydantic-settings`
2. `pip install pyngrok`

For using `ngrok`, start `uvicorn` server with your own args:
>`USE_NGROK=True python api.py --bind host --port port`

Note that `USE_NGROK=True` has been handled by the code and you can use this flag to use `ngrok` (online) or not (offline). Also, you can use `0.0.0.0` for the `host` to listen on all interfaces. By default we use `host=0.0.0.0` and `port=8000`.

----

#### 1.1.7 Install this package `cvfe`

Make sure you are in the root of the project, i.e. the same directory as the repo name. If you are in correct path, you should see `setup.py` containing information about `cvfe`.
>`pip install -e .`

### 2.2 Using Conda Environment File

We have provided a `yml` file (`conda_env.yml`) for ease of install using `conda` (or `mamba`). Please use:
> `conda env create -n YOUR_ENV_NAME --file conda_env.yml`

### 2.3 Using Docker

We have provided a `Dockerfile` for ease of install using `docker`. Please use:
> `docker build -t cvfe .`

*remark*: note that we do not use `mamba` in `Dockerfile` as the complexity of the environment is small and the overhead of installing `mamba` itself might not worth it. Nonetheless, *we never tested* this hypothesis and *appreciate your feedback*.
