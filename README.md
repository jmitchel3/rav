# rav

A cross-platform Python CLI to shortcut tp command-line commands. Inspired by Makefiles and npm scripts.


## Create a `rav.yaml` file

`rav.yaml`
```yaml
scripts:
    echo: echo "this is awesome"
    server: venv/bin/python -m http.server
```

Or if on windows:

`rav.yaml`
```yaml
scripts:
    echo: echo this is awesome
    win-server: venv\Scripts\python -m http.server
```

Or if you need a custom yaml file:

```yaml
rav:
    echo: echo "this is awesome"
    server: venv/bin/python -m http.server
```


## Basic Syntax

```
rav run <command>
```

`rav.yaml`:
```
scripts:
    <command>: echo "this is a command"
```

## Basic Example


`rav.yaml`:
```
scripts:
    hello: echo hello world!
```

```
rav run hello
```
By default, `rav run` will look for a `rav.yaml` file in the current directory.  You can customize it, with `-f` as explained [below](#custom-rav-file).


## Try the built-in Sample

```
rav sample create
```
This will output `rav.sample.yaml` in the current directory.

```
rav run -f rav.sample.yaml echo
```
`-f` is used to specify a custom rav file as documented [below](#custom-rav-file).


## Run a command

```
rav run echo
```

Or

```
rav run server
```

Or (if windows):

```
rav run win-server 8080
```

## Custom Rav File
Rav supports custom yaml files by default. The yaml declaration needs to be any of the following:

- `rav`
- `scripts`
- `commands`

`project.yaml`
```yaml
rav:
    sweet: echo "this is working"
    echo: echo "so is this"
```

`rav.basic.yaml`
```yaml
scripts:
    sweet: echo "this is working"
    echo: echo "so is this"
```

```
rav run -f project.yaml sweet
```
or
```
rav run --file rav.other.yaml echo
```

Here's a few rules for custom files:

- `-f` or `--file` is used to specify a custom rav file
- `-f` or `--file` must be used prior to the command shortcut name (e.g. `rav run -f <your-new-file> <your-command>`)


## Multiple Commands at Once

`rav.yaml`
```yaml
scripts:
    multi: 
        - echo this is
        - echo awesome
        - echo simple
        - echo and 
        - echo easy
```

Run with:

```
rav run multi
```

This is the same as running:

```
echo this is && echo awesome && echo simple && echo and && echo easy
```
