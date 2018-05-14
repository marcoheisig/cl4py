import json
import subprocess
import queue
import threading


def lisp_decoder(obj):
    if isinstance(object, dict):
        cls = obj[':class']
        if cls == 'CL:SYMBOL':
            return obj['package'] + '::' + obj['name']
        elif cls == obj['CL:CONS']:
            return (obj['car'], obj['cdr'])
        elif cls == 'CL:SIMPLE-VECTOR':
            return obj['contents']
        else:
            return obj


class Lisp:
    def __init__(self):
        global package
        cmd = ['ros', '-sp', 'cl-json', '-l', 'lisp.lisp', '-e', '(cl4py:cl4py)']
        self.subprocess = subprocess.Popen(cmd,
                                           stdin = subprocess.PIPE,
                                           stdout = subprocess.PIPE,
                                           stderr = subprocess.PIPE,
                                           shell = True)

    def lispify(self, obj):
        if isinstance(obj, tuple):
            result = False
            for elt in obj[::-1]:
                result = {'class' : 'CL:CONS',
                          'car' : lispify(elt),
                          'cdr' : result}
            return result
        else:
            return obj

    def pythonize(self, obj):
        return obj


    def roundtrip(self, obj):
        return json.loads(json.dumps(self.lispify(obj)),
                          object_hook=lisp_decoder)


    def eval(self, obj):
        print(json.dumps(obj, cls=LispEncoder))
        #json.dump(obj, self.subprocess.stdin)
        #values, dvars, error = json.load(self.subprocess.stdout)
