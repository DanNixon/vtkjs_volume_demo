#!/usr/bin/env python3

import sys
from flask import (
    Flask,
    Response,
    abort,
    request,
    send_from_directory
)
from flask_api import status
from io import BytesIO
from zipfile import ZipFile
import h5py
import json_tricks
import numpy as np


app = Flask('vtk_demo')


def dtype_to_vtkjs_type(dtype):
    """
    Converts a Numpy dtype to vtk.js type string.
    See https://kitware.github.io/vtk-js/docs/structures_DataArray.html#Structure
    """
    if dtype == np.int8:
        return 'Int8Array'
    if dtype == np.uint8:
        return 'Uint8Array'

    if dtype == np.int16:
        return 'Int16Array'
    if dtype == np.uint16:
        return 'Uint16Array'

    if dtype == np.int32:
        return 'Int32Array'
    if dtype == np.uint32:
        return 'Uint32Array'

    if dtype == np.float32:
        return 'Float32Array'
    if dtype == np.float64:
        return 'Float64Array'

    raise ValueError('Unknown dtype: {}'.format(dtype))


def dtype_byte_order_to_vtkjs_encode(dtype):
    """
    Determines endianness of dtype.
    If not explicity stated by the type then the system endianness is returned.
    See https://kitware.github.io/vtk-js/docs/structures_DataArray.html#Scalar-array-reference
    """
    endianness = {'<': 'little', '>': 'big'}.get(dtype.byteorder)
    if endianness is None:
        endianness = sys.byteorder
    return {'little': 'LittleEndian', 'big':'BigEndian'}[endianness]


def build_vtkjs_extents_array(array):
    extent = []
    for s in array.shape:
        extent.append(0)
        extent.append(s - 1)
    return extent


def load_volume_hdf5_array(filename, h5path):
    """
    Return some data.

    Data must not contain nans or infs (hence np.nan_to_num).
    Slicing is hacked into this function for the demo. Proper slicing is already in DAWN.
    """
    with h5py.File(filename) as f:
        step = 10
        return np.nan_to_num(np.array(f[h5path][380:1650:step, ::2, 400:1650:step]))


@app.route('/<path:path>')
def static_file(path):
    """
    Serve static files.
    Only used for demo.html
    """
    return send_from_directory('static', path)


@app.route('/data.zip')
def zip_data():
    filename = request.args.get('filename')
    h5path = request.args.get('path')

    if filename is None or h5path is None:
        abort(status.HTTP_400_BAD_REQUEST)

    # Load volume array
    volume = load_volume_hdf5_array(filename, h5path)

    # Create in memory Zip archive
    zip_buffer = BytesIO()
    zip_archive = ZipFile(zip_buffer, mode='w')

    # Generate metadata
    data = {
      "vtkClass": "vtkImageData",
      "metadata": {
        "name": filename,
      },
      "extent": build_vtkjs_extents_array(volume),
      "origin": [0.0] * volume.ndim,
      "spacing": [1.0] * volume.ndim,
      "pointData": {
        "arrays": [
          {
            "data": {
              "numberOfComponents": 1,
              "name": "ImageFile",
              "vtkClass": "vtkDataArray",
              "dataType": dtype_to_vtkjs_type(volume.dtype),
              "ranges": [
                {
                  "min": volume.min(),
                  "max": volume.max(),
                  "component": None,
                },
              ],
              "ref": {
                "registration": "setScalars",
                "id": "volume",
                "encode": dtype_byte_order_to_vtkjs_encode(volume.dtype),
                "basepath": "data",
              },
              "size": volume.size,
            }
          }
        ],
        "vtkClass": "vtkDataSetAttributes",
      },
    }

    # Generate metadata file
    metadata_file = BytesIO()
    metadata_file.write(bytearray(json_tricks.dumps(data), 'utf-8'))
    # Add metadata file to Zip archive
    zip_archive.writestr('index.json', metadata_file.getvalue())

    # Generate array binary file
    data_file = BytesIO()
    # Swap numpy array winding order to what VTK.js requires
    data_file.write(np.swapaxes(volume, 0, 2).data.tobytes())
    # Add array file to Zip archive
    zip_archive.writestr('data/volume', data_file.getvalue())

    zip_archive.close()

    return Response(zip_buffer.getvalue(), mimetype='application/octet-stream')


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
