import os
import shutil
import requests
import datetime
import time
import stat

def throw_error(operation, log, url, exception=None):
    requests.post(url, {
        "success": False,
        "log": "\n\n".join(log),
        "timestamp": datetime.datetime.now(),
        "exception": exception,
        "operation": operation
    })
    exit()

def manage_log(operation, current, url):
    try:
        data = None
        with open("out") as file:
            data = file.read()
        os.remove("out")
        if data is None or data == "":
            raise Exception("Data is undefined!")
        current.append(f"------ {operation} ------")
        current.append(data)
        return data
    except Exception as exception:
        throw_error(operation, current, url, str(exception))

def remove_error(function, path, execute):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

def build(**kwargs):
    start = time.time()
    output = []
    unit_tests_success = False
    setup_check_success = True
    twine_check_success = False
    url = kwargs["callback"]
    name = kwargs["name"]
    repository = kwargs["repository"]
    if os.path.isdir(name):
        shutil.rmtree(name, onerror=remove_error)
    os.system(f"git clone {repository} --progress 2> out")
    manage_log("Cloning Repository", output, url)
    if not os.path.isdir(name):
        throw_error("Cloning Repository", output, url)
    try:
        os.chdir(name)
        os.system("python setup.py develop > out")
        manage_log("Running Setup", output, url)
        os.system("python -m unittest 2> out")
        unit_tests = manage_log("Running Unit Tests", output, url)
        if "OK" in unit_tests:
            unit_tests_success = True
        os.system("python setup.py check > out")
        setup_check = manage_log("Checking Setup", output, url)
        if "warning" in setup_check or "error" in setup_check:
            setup_check_success = False
        os.system("python setup.py sdist > out")
        manage_log("Building Distribution", output, url)
        if not os.path.isdir("dist"):
            throw_error("Building Distribution", output, url)
        os.system("twine check dist/* > out")
        twine_check = manage_log("Checking Distribution", output, url)
        if "PASSED" in twine_check:
            twine_check_success = True
        os.chdir("..")
    except Exception as exception:
        throw_error("Main Process", output, url, exception)
    try:
        os.system(f"pip uninstall -y {name} > out")
        manage_log("Tearing Down", output, url)
        shutil.rmtree(name, onerror=remove_error)
    except Exception as exception:
        throw_error("Tear Down", output, url, exception)
    end = time.time()
    log = "\n\n".join(output)
    requests.post(url, {
        "success": True,
        "build": unit_tests_success and setup_check_success and twine_check_success,
        "log": log,
        "timestamp": datetime.datetime.now(),
        "duration": end - start,
        "unitTests": unit_tests_success,
        "setupCheck": setup_check_success,
        "twineCheck": twine_check_success,
        "pass": kwargs['pass']
    })
    try:
        if not os.path.isdir("logs"):
            os.mkdir("logs")
        file_name = f"logs/{str(time.time()).replace('.', '')}.log"
        with open(file_name, "w") as file:
            file.write(log)
    except Exception:
        pass
