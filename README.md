# Docsearch Scraper

Scrape documentation and push to Algolia Search. Available as a GitHub Action.

## Install

```shell
uv sync
```

## Set ENV

```shell
export APPLICATION_ID=<YOUR_APPLICATION_ID>
export API_KEY=<YOUR_API_KEY>
```

## Run

```shell
uv run python -m src.index <PRODUCT> <VERSION>

# Example
uv run python -m src.index broker v4.3
```

## Use as GitHub Action

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

## Links

- <https://github.com/algolia/docsearch-scraper>
