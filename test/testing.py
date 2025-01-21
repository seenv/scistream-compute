import time
import sys
from datetime import datetime

def testing(x):
    output = []
    output.append(f"script started {time.time()}")

    try:
        iterations = int(x)
        for iteration in range(iterations):
            output.append(f"Iteration {iteration + 1}, out of {x}")
            print(f"Iteration {iteration + 1}, out of {x}", flush=True)
            time.sleep(2)
    except ValueError:
        output.append(f"Error: Invalid input '{x}'")

    output.append(f"script finished {time.time()}")
    return "\n".join(output)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "no arg!!!!"
    print(datetime.now().strftime("%H:%M:%S"))
    testing(arg)
    #print(testing(arg))

