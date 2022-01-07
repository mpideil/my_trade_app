#!/bin/python
import json

class Result:
    # 2 = Critical
    # 1 = Warning
    # 0 = ok
    status=0
    msg=None
    val=None
    empty=False

    def __init__(self,status=0,msg="",value=[],empty=False):
        self.status = status
        self.msg = msg
        self.value = value
        self.empty=empty
    @classmethod
    def ok(cls,value=[],msg=''):
        return cls(status=0,msg=msg,value=value)
    @classmethod
    def error(cls,value=[],msg=''):
        return cls(status=1,msg=msg,value=value)
    @classmethod
    def warn(cls,value=[],msg=''):
        return cls(status=2,msg=msg,value=value)
    @classmethod
    def critical(cls,value=[],msg=''):
        return cls(status=3,msg=msg,value=value)
    @classmethod
    def empty(cls,value=[],msg=''):
        return cls(status=4,msg=msg,value=value,empty=True)
    def __eq__(self, other):
        if (isinstance(other, Result)):
            return self.status == other.status and self.value == other.value
        return False
    def __repr__(self):
        return str(self.__dict__)
    def __str__(self):
        return "Result instance :\n"+str(self.__dict__)
    def __bool__(self):
        if self.status == 0:
            return True
        else:
            return False