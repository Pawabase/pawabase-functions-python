# pawabase-functions

The function kit for [Pawabase](https://github.com/Pawabase/pawabase): write custom **functions** in your own repository (Python or TypeScript), test them
without a server, **deploy** them with an API key, and **emulate** them on your machine against a real deployment. It installs the `pawabase` command.

It is the *authoring* side. To call Pawabase from an app (records, auth, storage, realtime…), use the client SDK: [`pawabase`](../python) on PyPI,
`@pawabase/client` on npm. TypeScript functions have their own kit, `@pawabase/functions`, in [pawabase-js](https://github.com/Pawabase/pawabase-js).

It needs `pawabase` (the client, for HTTP) and Python 3.11+. It contains no server code.

```bash
pip install pawabase-functions        # also installs the pawabase client
pawabase --version
```

## Quick start

```bash
pawabase init                  # functions/hello.py, tests/test_hello.py, .env.example
pawabase link -e development  # writes pawabase.toml (url, environment): never the key
echo 'PAWABASE_URL=https://api.example.com'   >> .env
echo 'PAWABASE_API_KEY=pb_sk_...'             >> .env     # a SECRET key of the environment

pawabase test                  # unit tests, no server needed
pawabase emulate --watch       # run locally against the deployment, on http://127.0.0.1:8787
pawabase deploy                # upload and activate
```

## A function

```python
# functions/hello.py
from pawabase.functions import FunctionError, function

@function("hello", policy="public", input_fields=[{"name": "name", "type": "string"}])
async def hello(ctx):
    name = ctx.input.get("name") or "world"
    if name == "nobody":
        raise FunctionError("Say hello to someone.", status=422, code="no_one")
    ctx.log("greeting", name=name)
    await ctx.runtime.emit("greeted", {"name": name})
    return {"message": f"Hello, {name}!"}
```

The same file runs on a deployment, under `pawabase emulate`, and in a test:

```python
from pawabase.testing import FakeRuntime, call

async def test_hello():
    runtime = FakeRuntime()
    result = await call("hello", {"name": "Ada"}, runtime=runtime, project_dir="functions")
    assert result.ok and result.result == {"message": "Hello, Ada!"}
    assert runtime.emitted == [("greeted", {"name": "Ada"})]
```

`FakeRuntime` runs real SQL on in-memory SQLite and records events, queued flows and functions, mail, outbound HTTP and storage writes.

## Commands

| Command | |
| --- | --- |
| `pawabase deploy [--branch NAME \| --git-branch] [--dry-run] [--force] [-y]` | Check, bundle and upload your functions. Refuses broken code and credentials. Says "No changes" if nothing changed |
| `pawabase emulate [--watch] [--port 8787]` | A local gateway: your functions run here, everything else is forwarded to the deployment |
| `pawabase trigger event\|schedule\|flow NAME [-d JSON]` | Fire one; subscribers run where their code lives |
| `pawabase invoke NAME [-d JSON] [--local] [--as-user ID]` | Call the deployed function, or your local copy |
| `pawabase functions \| deployments \| rollback \| branches \| logs [-f]` | Inspect and operate |
| `pawabase login \| logout \| link \| init \| whoami \| test` | Setup |

Settings come from flags, `PAWABASE_URL`, `PAWABASE_API_KEY`, `PAWABASE_ENVIRONMENT`, `PAWABASE_BRANCH`, a git-ignored `.env`, `pawabase.toml`, and
`pawabase login`, in that order. The key is never written to `pawabase.toml`.

Exit status: `0` success, `1` the operation failed, `2` something is missing or misspelled.

## TypeScript

A project's functions are one language. `pawabase init --typescript` makes `functions/hello.ts`; `pawabase deploy` bundles it, and the deployment runs it in
Deno (the TypeScript is loaded and checked there). Write them with [`@pawabase/functions`](https://github.com/Pawabase/pawabase-js/tree/main/functions) for types.
A folder with both `.py` and `.ts` files is refused.

## Calling Pawabase

The `pawabase` client SDK does that. This package adds the calls only a function author needs, on `pawabase.kitclient.KitClient` /
`AsyncKitClient` (deploy a bundle, read run logs, run a function or a flow as an operator, execute `ctx.runtime` on the deployment).

## Documentation

- Writing functions: [`code/functions.mdx`](https://github.com/Pawabase/pawabase-docs/blob/main/code/functions.mdx)
- The command line, deploying, emulating: [`code/cli.mdx`](https://github.com/Pawabase/pawabase-docs/blob/main/code/cli.mdx)

## Develop

```bash
git clone https://github.com/Pawabase/pawabase-python && cd pawabase-python
pip install -e ../python -e .[test]    # both packages, editable
python -m pytest
uv build                             # wheel and sdist into dist/
```

BSD 3-Clause licensed.
