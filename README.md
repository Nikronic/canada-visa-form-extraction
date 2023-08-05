# Canada Visa Form Extraction

**C**anada **V**isa **F**orm **E**xtraction (`CVFE`) is a tool set to extract and transform Canada visa forms (**IMM 5257 E** and **IMM 5645 E**) into standard format.

## 1 Installation

### 1.1 Package

#### 1.1.1 PIP

`pip install git+https://github.com/Nikronic/canada-visa-form-extraction.git`

Or if you have cloned/downloaded the repository already, just use `pip install .`

#### 1.1.2 Using Conda Environment File

We have provided a `yml` file (`conda_env.yml`) for ease of install using `conda` (or `mamba`). Please use:
> `conda env create -n YOUR_ENV_NAME --file conda_env.yml`

#### 1.1.3 Using Docker

**Official Image**:
The easiest way is to just pull the official image from GitHub Container Registry:
> `docker pull ghcr.io/nikronic/cvfe:DESIRED_VERSION`

For instance, for the version `v0.2.1` (`cat VERSION`), you can pull `docker pull ghcr.io/nikronic/cvfe:v0.2.1`.

Then for running it, use:
> `docker run -p YOUR_HOST_PORT:CONTAINER_PORT ghcr.io/nikronic/cvfe:DESIRED_VERSION python -m cvfe.main --bind 0.0.0.0 --port CONTAINER_PORT`

For example:
> `docker run -p 9999:8000 ghcr.io/nikronic/cvfe:v0.2.1 python -m cvfe.main --bind 0.0.0.0 --port 8000`

*note:* All the images can be found on the [repo packages](https://github.com/Nikronic/canada-visa-form-extraction/pkgs/container/cvfe).

**Manual Image**:
We have provided a `Dockerfile` for ease of install using `docker`. Please use:
> `docker build -t cvfe .`

For running it, you need to map the port `8000` of the container to your desired port (`8001`) on host:
> `docker run -p 8001:8000 cvfe`

*remark*: note that we do not use `mamba` in `Dockerfile` as the complexity of the environment is small and the overhead of installing `mamba` itself might not worth it. Nonetheless, *we never tested* this hypothesis and *appreciate your feedback*.

### 1.2 Manual Installation

Using `conda` as the package manager is not necessary nor provides any advantages (of course virtual environment are necessary). Hence, if you like, you can install dependencies via `conda`. Note that only few of the dependencies are available on `conda` channels and you still need to use `pip`.

From now on, the phrase "*if conda*" assumes if you are using `conda` for your packages. Otherwise, `pip` only is inferred.

**tip:** You can use `mamba` to hugely speed up the installation process. If you don't want to, replace all instances of the `mamba` with `conda` in following steps.

#### \[Optional\] 1.2.1 Create a `conda` env

> if conda: `conda create --name cvfe python=3.11.0 -y`

#### \[Optional\] 1.2.2 Activate the new environment

Make sure you activate this environment right away:
> if conda: `conda activate cvfe`

#### 1.2.3 Update `pip`

You should have at least `pip >= 23.1.2`
> `pip install --upgrade pip`

#### \[Optional\] 1.2.4 Pin the Python version

When using `conda`, `mamba` and so on, it might update the Python to its latest version. We should prevent that by pinning the Python version in the `conda` environment. To do so:

> if conda: `echo "python 3.11.0" >>$CONDA_PREFIX/conda-meta/pinned`

#### 1.2.5 Install Processing Dependencies

We need `pandas` and `numpy` and some others, but installing `pandas` will install all those needed.

> `pip install pandas`
> if conda: `mamba install pandas`

#### 1.2.5 Install data extraction dependencies

> 1. `pip install xmltodict>=0.13.0`. if conda: `mamba install -c conda-forge xmltodict>=0.13.0 -y`
> 2. `pip install pikepdf>=5.1.5`
> 3. `pip install pypdf2>=2.2.1`

#### 1.2.6 Install API libs

These libraries (the main one is FastAPI) are not for the ML part and only are here to provide the API and web services.

>1. `pip install pydantic>=1.9.1`
>2. `pip install fastapi>=0.85.0`
>3. `pip install gunicorn>=20.1.0`
>4. `pip install uvicorn>=0.18.2`
>5. `pip install python-multipart>=0.0.5`

*\[Optional\]* For making it online (only for development) using `ngrok`:

1. `pip install pydantic-settings`
2. `pip install pyngrok`

For using `ngrok`, start `uvicorn` server with your own args:
>`USE_NGROK=True python api.py --bind host --port port`

Note that `USE_NGROK=True` has been handled by the code and you can use this flag to use `ngrok` (online) or not (offline). Also, you can use `0.0.0.0` for the `host` to listen on all interfaces. By default we use `host=0.0.0.0` and `port=8000`.

----

#### 1.2.7 Install this package `cvfe`

Make sure you are in the root of the project, i.e. the same directory as the repo name. If you are in correct path, you should see `setup.py` containing information about `cvfe`.
>`pip install -e .`
