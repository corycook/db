from string import join
from random import random
from collections import OrderedDict as dict
import pypyodbc

class Parameter:
    def __init__(self, prefix, join=', ', suffix=''):
        self.prefix = prefix
        self.join = join
        self.suffix = suffix
        self.parameters = dict()
        self.index = 0
    
    def add(self, column, argument=None):
        if argument is None:
            self.parameters[self.index] = column
            self.index += 1
        else:
            self.parameters[column] = argument

    def reset(self):
        self.parameters.clear()

    def serialize(self):
        if len(self.parameters):
            return self.prefix + join(self.parameters.values(), self.join) + self.suffix
        return None

class ValuesParameter(Parameter):
    def __init__(self, prefix, join=', ', suffix=''):
        return Parameter.__init__(self, prefix, join, suffix)

    @staticmethod
    def stringset(value):
        if isinstance(value, str):
            return '\'' + value + '\''
        else:
            return value

class SearchParameter(ValuesParameter):
    def __init__(self):
        return ValuesParameter.__init__(self, ' WHERE ', ' AND ')

    @staticmethod
    def set(value, key):
        if isinstance(key, int):
            return str(value)
        elif isinstance(value, str):
            return str(key) + ' LIKE ' + value
        elif isinstance(value, list):
            for i in value:
                i = ValuesParameter.stringset(i)
            return key + ' IN (' + join(value, ', ') + ')'
        elif isinstance(value, DbEngine):
            return str(key) + ' IN (' + value.tosql() + ')'
        else:
            return str(key) + '=' + str(value)

    def serialize(self):
        if len(self.parameters):
            for key, value in self.parameters.items():
                value = ValuesParameter.stringset(value)
                self.parameters[key] = SearchParameter.set(value, key)
            return ValuesParameter.serialize(self)
        return None

class SetParameter(ValuesParameter):
    def __init__(self):
        return ValuesParameter.__init__(self, ' SET ')

    @staticmethod
    def set(value, key):
        return str(key) + "=" + str(value)

    def serialize(self):
        if len(self.parameters):
            for key, value in self.parameters.items():
                value = SetParameter.stringset(value)
                self.parameters[key] = SetParameter.set(value, key)
            return ValuesParameter.serialize(self)
        return None

class SelectParameter(Parameter):
    def __init__(self):
        Parameter.__init__(self, 'SELECT ')
    def serialize(self):
        if len(self.parameters):
            return Parameter.serialize(self)
        else:
            return self.prefix + '*'

class DbEngine:
    def __init__(self, db, FromParameter = None):
        self.connection = pypyodbc.connect(db)
        self.cursor = self.connection.cursor()
        self.parameters = dict()
        self.refresh()
    
    def __del__(self):
        self.connection.close()

    def tosql(self):
        sql = ''
        for key, parameter in self.parameters.items():
            if isinstance(parameter, Parameter):
                val = parameter.serialize()
                if val is not None and isinstance(val, str):
                    sql += val
        return sql

    def parameter(self, param, col=None, arg=None):
        if isinstance(col, list) and isinstance(arg, list):
            if len(col) == len(arg):
                for i in range(1, len(col)):
                    self.parameter(param, col[i], arg[i])
        elif isinstance(col, list):
            for i in col:
                self.parameter(param, i, arg)
        else:
            self.parameters[param].add(col, arg)


    def table(self, tbl=None, alias=None):
        self.tablename = tbl
        self.parameter('from', tbl, alias)
        return self

    def search(self, col=None, arg=None):
        self.parameter('search', col, arg)
        return self

    'def toarray():'

    def result(self):
        if self.state == self.checkstate:
            return self.cursor
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.tosql())
        self.checkstate = self.state
        return self.cursor

    'def count():'

    def refresh(self):
        self.state = random()
        if self.cursor is not None:
            self.cursor.close()

class SelectEngine(DbEngine):
    def __init__(self, db):
        DbEngine.__init__(self, db)
        self.parameters.setdefault('select', SelectParameter())
        self.parameters.setdefault('from', Parameter(' FROM '))
        self.parameters.setdefault('search', SearchParameter())
        self.parameters.setdefault('group', Parameter(' GROUP BY '))
        self.parameters.setdefault('sort', Parameter(' ORDER BY '))

    def group(self, col=None):
        self.parameter('group', col)
        return self

    def sort(self, col=None):
        self.parameter('sort', col)
        return self

    def select(self, col=None):
        self.parameter('select', col)
        return self

class InsertEngine(DbEngine):
    def __init__(self, db):
        DbEngine.__init__(self, db)
        self.parameters.setdefault('from', Parameter('INSERT INTO '))
        self.parameters.setdefault('keys', Parameter(' (', ', ', ')'))
        self.parameters.setdefault('values', ValuesParameter(' VALUES (', ', ', ')'))

    def insert(self, object):
        if isinstance(object, dict):
            for key, value in object.items():
                self.parameter('keys', key)
                self.parameter('values', value)
            return self.result()

class UpdateEngine(DbEngine):
    def __init__(self, db):
        DbEngine.__init__(self, db)
        self.parameters.setdefault('from', Parameter('UPDATE '))
        self.parameters.setdefault('set', SetParameter())
        self.parameters.setdefault('search', SearchParameter())

    def update(self, object):
        if isinstance(object, dict):
            for key, value in object:
                self.parameter('set', key, value)
            return self.result()

class DeleteEngine(DbEngine):
    def __init__(self, db):
        DbEngine.__init__(self, db)
        self.parameters.setdefault('from', Parameter('DELETE FROM '))
        self.parameters.setdefault('search', SearchParameter())

    def delete(self):
        return self.result()

class Db(SelectEngine):
    def insert(self, object):
        Engine = InsertEngine(self)
        Engine.insert(object)
    def update(self, object):
        Engine = UpdateEngine(self)
        Engine.update(object)
    def delete(self):
        Engine = DeleteEngine(self)
        Engine.delete()
