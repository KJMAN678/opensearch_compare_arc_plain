### Devin

- [Devin's Machine](https://app.devin.ai/workspace) でリポジトリ追加

#### 1.Git Pull
- そのまま

#### 2.Configure Secrets
```sh
# 環境変数用のファイル作成
$ touch .envrc

# .envrc に下記を入力. xxx は適宜更新

export DJANGO_SUPERUSER_USERNAME=xxx
export DJANGO_SUPERUSER_EMAIL=xxx@xxx.com
export DJANGO_SUPERUSER_PASSWORD=xxx

# 環境変数を読み込む
$ direnv allow
```

- ローカル用
```sh
$ brew install direnv
```
#### 4.Maintain Dependencies
```sh
$ uv venv && . .venv/bin/activate && uv pip install -U pip && uv pip sync requirements.txt
```

#### 5.SetUp Lint
```sh
$ uvx ruff check
```

#### 6.SetUp Tests
- no tests ran in 0.00s だと Devin の Verify が通らないっぽい
```sh
$ uvx pytest
```

### 7.Setup Local App

```sh
$ Run uv run manage.py migrate && uv run manage.py createsuperuser --noinput && uv run python manage.py runserver
$ http://127.0.0.1:8000/ がローカルサーバーのURL

$ uv run manage.py makemigrations
$ uv run manage.py migrate
$ uv run manage.py createsuperuser --noinput
$ uv run python manage.py runserver
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
