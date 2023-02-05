# rav

A cross-platform approach to executing shortcut commands.


## Create a `rav.yaml` file

`rav.yaml`
```
scripts:
    echo: echo "this is awesome"
    server: venv/bin/python -m http.server
```


## Run a script

```
rav run echo
```

or
    
```
rav run server
```

## Create an example project

```
rav sample create
```