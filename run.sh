#!/bin/bash

python -m pip uninstall -y MMSA
python -m pip install .

python run.py