import sys
import os

log_file = os.path.join(os.getenv('APPDATA'), 'CAPM', 'logs', 'startup_diag.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

with open(log_file, 'w') as f:
    f.write("Startup diagnosis begin\n")
    f.write(f"Python: {sys.version}\n")
    
    try:
        import numpy
        f.write(f"Numpy: {numpy.__version__}\n")
    except Exception as e:
        f.write(f"Numpy failed: {e}\n")

    try:
        import pandas
        f.write(f"Pandas: {pandas.__version__}\n")
    except Exception as e:
        f.write(f"Pandas failed: {e}\n")

    try:
        import scipy
        f.write(f"Scipy: {scipy.__version__}\n")
    except Exception as e:
        f.write(f"Scipy failed: {e}\n")
        
    try:
        import statsmodels.api
        f.write("Statsmodels loaded\n")
    except Exception as e:
        f.write(f"Statsmodels failed: {e}\n")

    f.write("Startup diagnosis end\n")

print("Diagnosis complete")
