### 起動

```sh
$ touch .envrc

export OPENSEARCH_INITIAL_ADMIN_PASSWORD=hoge
export DJANGO_SUPERUSER_USERNAME=hoge
export DJANGO_SUPERUSER_EMAIL=hoge@hoge.com
export DJANGO_SUPERUSER_PASSWORD=hoge
export SECRET_KEY=hoge
```

```sh
$ direnv allow

$ docker compose up -d
$ docker compose down
$ docker compose build
```


### Devin

- [Devin's Machine](https://app.devin.ai/workspace) でリポジトリ追加

#### 1.Git Pull
- そのまま

#### 2.Configure Secrets
```sh
# 環境変数用のファイル作成
$ touch .envrc

# .envrc に下記を入力. xxx は適宜更新

export OPENSEARCH_INITIAL_ADMIN_PASSWORD=hoge
export DJANGO_SUPERUSER_USERNAME=hoge
export DJANGO_SUPERUSER_EMAIL=hoge@hoge.com
export DJANGO_SUPERUSER_PASSWORD=hoge
export SECRET_KEY=hoge

# 環境変数を読み込む
$ direnv allow
```

- ローカル用
```sh
$ brew install direnv
```
#### 4.Maintain Dependencies
```sh
$ docker compose up -d
```

#### 5.SetUp Lint
```sh
$ docker compose run --rm web uv run ruff check
```

#### 6.SetUp Tests
- no tests ran in 0.00s だと Devin の Verify が通らないっぽい
```sh
$ docker compose run --rm web uv run pytest
```

### 7.Setup Local App

```sh
$ Run uv run manage.py migrate && uv run manage.py createsuperuser --noinput && uv run python manage.py runserver
$ http://127.0.0.1:8000/ がローカルサーバーのURL

$ docker compose run --rm web uv run manage.py makemigrations
$ docker compose run --rm web uv run manage.py migrate
$ docker compose run --rm web uv run manage.py createsuperuser --noinput
$ docker compose run --rm web uv run manage.py runserver
```
http://127.0.0.1:8000/

#### 8.Additional Notes
- 必ず日本語で回答してください
を入力

### OPENAI-API で PR-Review
- [Qodo Merge](https://qodo-merge-docs.qodo.ai/installation/github/)
  - GPT-4.1利用
  - 日本語の回答をするようプロンプト設定
- GitHub の Repository >> Settings >> Secretes and variables >> Actions の Repository secrets の New repository secret を登録
  - OPENAI_KEY という名称で OPENAI API keys の SECRET KEY を登録
    - [OPENAI API keys](https://platform.openai.com/settings/organization/api-keys) 
```sh
--- .github/
           |- workflows/
                        |-- pr_agent.yml
```
