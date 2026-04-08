# Docsearch Scraper For Docs

## Install
```shell
pipenv install --keep-outdated
pipenv shell
```

## Set ENV
```shell
export APPLICATION_ID=<YOUR_APPLICATION_ID>
export API_KEY=<YOUR_API_KEY>
```

## Run
```shell
python3 -m src.index <CONFIG_FILE_NAME> <PRODUCT> <VERSION>

python3 -m src.index config broker v4.3
```

> `CONFIG_FILE_NAME`: `config`
## Links
- <https://github.com/algolia/docsearch-scraper>


## Use for GitHub action
```yaml
      - name: update search index
        uses: emqx/docsearch-scraper@main
        env:
          APPLICATION_ID: ${{ secrets.ALGOLIA_APPLICATION_ID_NEXT }}
          API_KEY: ${{ secrets.ALGOLIA_API_KEY_NEXT }}
          BASE_URL: https://docs.emqx.com
        with:
          docs_type: ${{ env.DOCS_TYPE }}
          docs_version: ${{ env.VERSION }}
```
