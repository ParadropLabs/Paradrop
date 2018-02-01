# Building

python setup.py sdist
python setup.py bdist_wheel --universal

# Uploading to pypi

Make sure the dist directory is clean and run:

twine upload dist/*

Reference: https://packaging.python.org/tutorials/distributing-packages/
