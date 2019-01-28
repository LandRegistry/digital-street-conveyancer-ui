export CUSTOM_COMPILE_COMMAND="./pipcompilewrapper.sh"
rm requirements.txt
pip-compile --output-file requirements.txt requirements.in
pip-compile --upgrade
