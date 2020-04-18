import os
import shutil
import requests
import datetime
import time
import stat

class Helper:
    def __init__(self, url, return_token, pass_through):
        self._url = url
        self._return_token = return_token
        self._pass_through = pass_through

    def throw_error(self, operation, log, exception=None):
        requests.post(self._url, {
            "success": "false",
            "log": "\n\n".join(log),
            "timestamp": str(datetime.datetime.now()).split(".")[0],
            "exception": exception,
            "operation": operation,
            "pass": self._pass_through
        }, headers={
            "API-Route": "Build",
            "API-Token": self._return_token
        })
        exit()

    def manage_log(self, operation, current):
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
            self.throw_error(operation, current, str(exception))

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
    return_token = kwargs["return"]
    repository = kwargs["repository"]
    pass_through = kwargs["pass"]
    helper = Helper(url, return_token, pass_through)
    if os.path.isdir(name):
        shutil.rmtree(name, onerror=remove_error)
    os.system(f"git clone {repository} --progress 2> out")
    helper.manage_log("Cloning Repository", output)
    if not os.path.isdir(name):
        helper.throw_error("Cloning Repository", output)
    try:
        os.chdir(name)
        os.system("python setup.py develop > out")
        helper.manage_log("Running Setup", output)
        os.system("python -m unittest 2> out")
        unit_tests = helper.manage_log("Running Unit Tests", output)
        if "OK" in unit_tests:
            unit_tests_success = True
        os.system("python setup.py check > out")
        setup_check = helper.manage_log("Checking Setup", output)
        if "warning" in setup_check or "error" in setup_check:
            setup_check_success = False
        os.system("python setup.py sdist > out")
        helper.manage_log("Building Distribution", output)
        if not os.path.isdir("dist"):
            helper.throw_error("Building Distribution", output)
        os.system("twine check dist/* > out")
        twine_check = helper.manage_log("Checking Distribution", output)
        if "PASSED" in twine_check:
            twine_check_success = True
        os.chdir("..")
    except Exception as exception:
        helper.throw_error("Main Process", output, exception)
    try:
        os.system(f"pip uninstall -y {name} > out")
        helper.manage_log("Tearing Down", output)
        shutil.rmtree(name, onerror=remove_error)
    except Exception as exception:
        helper.throw_error("Tear Down", output, exception)
    end = time.time()
    log = "\n\n".join(output)
    requests.post(url, {
        "success": "true",
        "build": "true" if unit_tests_success and setup_check_success and twine_check_success else "false",
        "log": log,
        "timestamp": str(datetime.datetime.now()).split(".")[0],
        "duration": end - start,
        "unitTests": "true" if unit_tests_success else "false",
        "setupCheck": "true" if setup_check_success else "false",
        "twineCheck": "true" if twine_check_success else "false",
        "pass": pass_through
    }, headers={
      "API-Route": "Build",
      "API-Token": return_token
    })
    try:
        if not os.path.isdir("logs"):
            os.mkdir("logs")
        file_name = f"logs/{str(time.time()).replace('.', '')}.log"
        with open(file_name, "w") as file:
            file.write(log)
    except Exception:
        pass
