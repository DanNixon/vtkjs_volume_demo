# VTK.js volume demo

## Data

Add the output of a Savu reconstruction in the `data` directory and change the
filename used in `static/demo.html`.

## Running

With Docker:
```sh
./run.sh
```

Without Docker:
```sh
pip install -r requirements.txt
./server.py
```

A page will be served at `localhost:5000/demo.html` which renders the volume in
the final output of the data file provided.
