"""
test_1.py

a test of decorator funcitons


By: Calacuda | MIT Licence | Epoch: Sept 11, 2022
"""

# function types
# import types
from types import FunctionType, BuiltinFunctionType, LambdaType

# method types
from types import MethodType, BuiltinMethodType, BuiltinMethodType, MethodDescriptorType
import os
from datetime import datetime as dt


class LogData:
    def __init__(self):
        self._level = None  # info, log, debug, error, panic
        self.obj_name: str = None
        self.obj_args: list = None
        self.obj_kwargs: dict = None
        self.obj_type: str = None  # function, method, class
        self.return_val = None

    def __repr__(self):
        return self

    def __str__(self):
        lvl = self._make_level()

        # set interact message
        if self.obj_type.lower() != "class":
            interact_verb = "called"
        else:
            interact_verb = "instantiated"

        # make comma separated string list of all the arguemnts sent to the obj/func
        all_args = [f"\"{arg}\"" if type(arg) == str else str(arg) for arg in self.obj_args]
        [all_args.append(f"{name}={self.kwargs.get(val)}") for name in self.obj_kwargs.keys()]
        args = ", ".join(all_args)
        
        # make data about the data returned by the obj
        return_type = f"{type(self.return_val)}"
        return_value = f"<{self.return_val}>"        
        
        msg = f"{dt.now().isoformat()} | {lvl} {self.obj_type} <{self.obj_name}> {interact_verb}: {self.obj_name}({args}) => {return_type} {return_value}" 

        return msg

    def set_return_val(self, value):
        self.return_val = "value"
    
    def set_level(self, level):
        match level.lower():
            case "info":
                self._level = "info"
            case "log":
                self._level = "log"
            case "debug":
                self._level = "debug"
            case "error":
                self._level = "error"
            case "panic":
                self._level = "panic"
            case other:
                print(f"\"{level}\" is not a valid log level.")
                print("try one of the following: info, log, debug, error, panic")

    def _obj_is_type(self, obj, types):
        for type in types:
            if isinstance(obj, type):
                return True

        return False

    def set_obj(self, obj):
        self.obj_name = obj.__name__
        types_meta = [
                [FunctionType, BuiltinFunctionType, LambdaType], 
                [MethodType, BuiltinMethodType, BuiltinMethodType, MethodDescriptorType],
                ]
        names_meta = ["Function", "Method"]

        for name, types, in zip(names_meta, types_meta):
            # print(f"name :  {name}, types :  {types}")
            if self._obj_is_type(obj, types):
                self.obj_type = name
                return

        self.obj_type = "Class"

    def _make_level(self):
        return f"[{self._level.upper()}]"


class Logger:
    def __init__(self, log_file=None, debug=False, io_stream=None, logging=True):
        self.logf = log_file
        self.debug = debug
        self._level = "log"
        self.io = io_stream
        self.logging = logging

    def set_level(self, level):
        match level.lower():
            case "info":
                self._level = "info"
            case "log":
                self._level = "log"
            case "debug":
                self._level = "debug"
            case "error":
                self._level = "error"
            case "panic":
                self._level = "panic"
            case other:
                print(f"\"{level}\" is not a valid log level.")
                print("try one of the following: info, log, debug, error, panic")
        return self

    def record(self, data):
        """writes the log data to the log file, or prints to self.io if io_stream was set to stderr or stdout"""
        if self.io is not None:
            print(data, file=self.io)

        if not os.path.exists(self.logf):
            open(self.logf, 'w').close()
        
        with open(self.logf, "a") as f:
            f.write(str(data))
            f.write("\n")
        
    def log(self, func):
        data = LogData()
        data.set_obj(func)

        def wrapper(*args, **kwargs):
            if self.logging:               
                data.obj_args = args
                data.obj_kwargs = kwargs

                try:
                    value = func(*args, **kwargs)
                except Exception as e:
                    data.set_level("Error")
                    self.record(data)
                    raise e
                else:
                    data.set_level(self._level)
            
                data.return_val = value
                
                if self.debug: 
                    self.record(data)
            else:
                value = func(*args, **kwargs)

            return value
        
        return wrapper


import sys


logger = Logger(debug=True, logging=True, io_stream=sys.stderr, log_file= "log.txt")


@logger.log
def greet(name):
    print(f"Hello and well met {name.title()}.")


if __name__ == "__main__":
    greet("yogurt")
