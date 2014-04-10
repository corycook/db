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

    def serialize(self, values=None):
        if len(self.parameters):
            if values is None:
                values = self.parameters.values()
            return self.prefix + join(values, self.join) + self.suffix
        return None

class ValuesParameter(Parameter):
    def __init__(self, prefix, join=', ', suffix=''):
        return Parameter.__init__(self, prefix, join, suffix)

    def set(self, value, key):
        return value

    @staticmethod
    def stringset(value):
        if isinstance(value, str):
            return '\'' + value + '\''
        else:
            return value

    def serialize(self):
        if len(self.parameters):
            values = []
            for key, value in self.parameters.items():
                values.append(self.set(ValuesParameter.stringset(value), key))
            return Parameter.serialize(self, values)
        return None

class SearchParameter(ValuesParameter):
    def __init__(self):
        return ValuesParameter.__init__(self, ' WHERE ', ' AND ')

    def set(self, value, key):
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

class SetParameter(ValuesParameter):
    def __init__(self):
        return ValuesParameter.__init__(self, ' SET ')

    def set(self, value, key):
        return str(key) + "=" + str(value)

class SelectParameter(Parameter):
    def __init__(self):
        Parameter.__init__(self, 'SELECT ')
    def serialize(self):
        if len(self.parameters):
            return Parameter.serialize(self)
        else:
            return self.prefix + '*'

class DbEngine:
    def __init__(self, db, FromParameter=None):
        if isinstance(db, DbEngine):
            self.connection = pypyodbc.connect(db.connection.connectString)
        else:
            self.connection = pypyodbc.connect(db)
        self.cursor = self.connection.cursor()
        self.parameters = dict()
        self.state = random()
        self.checkstate = random()
        self.refresh()
    
    def __del__(self):
        if self.connection.connected:
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
        if col is None:
            self.parameters[param].reset()
        elif isinstance(col, list) and isinstance(arg, list):
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

    def toarray(self):
        return self.result().fetchall()

    def result(self):
        if self.state == self.checkstate:
            return self.cursor
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.tosql())
        self.checkstate = self.state
        return self.cursor

    def count(self, db=None):
        if db is None:
            db = Db(self)
        db.select()
        db.select('count(*) as count')
        return db.result().fetchall()[0]['count']

    def refresh(self):
        self.state = random()
        if self.cursor is not None:
            self.cursor.close()
        return self

class SelectEngine(DbEngine):
    def __init__(self, db):
        DbEngine.__init__(self, db)
        self.parameters.setdefault('select', SelectParameter())
        if isinstance(db, DbEngine):
            self.parameters.setdefault('from', db.parameters['from'])
            self.parameters.setdefault('search', db.parameters['search'])
        else:
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
        if isinstance(db, DbEngine):
            self.parameters['from'].parameters = db.parameters['from'].parameters

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
        if isinstance(db, DbEngine):
            self.parameters['from'].parameters = db.parameters['from'].parameters
            self.parameters['search'].parameters = db.parameters['search'].parameters

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
        if isinstance(db, DbEngine):
            self.table(db.tablename)
            self.parameters['search'].parameters = db.parameters['search'].parameters

    def delete(self):
        return self.result()

class Db(SelectEngine):
    def insert(self, object):
        InsertEngine(self).insert(object)
    def update(self, object):
        UpdateEngine(self).update(object)
    def delete(self):
        DeleteEngine(self).delete()
