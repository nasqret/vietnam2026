set -euo pipefail
ulimit -t 15
ulimit -v 1048576
module purge
module load Python/3.11.5
exec python3 -I -B -c 'import ctypes,ssl,zlib,json,os,sys; print(json.dumps({'"'"'python'"'"':sys.executable,'"'"'version'"'"':sys.version,'"'"'ctypes'"'"':ctypes.__file__,'"'"'ssl'"'"':ssl.__file__,'"'"'ld_library_path'"'"':os.environ.get('"'"'LD_LIBRARY_PATH'"'"'),'"'"'loaded_modules'"'"':os.environ.get('"'"'LOADEDMODULES'"'"'),'"'"'gpu_allocations'"'"':0,'"'"'model_imports'"'"':False}))'
