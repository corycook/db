db
==

SQL Generator Libraries

The Db Sql Generator Libraries provide a simple interface that abstracts SQL queries from your code and provides an object-oriented approach to database interaction.

PHP Usage
---------

Be sure to include the library:
```php
<?php

include('db.php');

?>
```

Create the Db object and connect to the database:
```php
$db = new Db('connectionNameOrString', 'username', 'password');
```

To copy connection, table, and search information:
```php
$db2 = new Db($db);
```

Select a table to perform actions on:
```php
$db->from('tableName');
```

To display as an HTML table:

```php
$db->table();
```

To retrieve generated SQL command:

```php
$db->buildsql();
```

To retrieve a result as an array:

```php
$db->toarray();
```

To search for a string on a column:

```php
$db->search('columnName', 'value');
```

To search for values on multiple columns:

```php
$db->search('column1Name', 'column1Value');
$db->search('column2Name', 'column2Value');
```
or
```php
$db->search(array('column1Name', 'column2Name'),
  array('column1Value', 'column2Value');
```

To search for a number (e.g. 1) on a column:

```php
$db->search('columnName', 1);
```

To match a value in a set of values:

```php
$db->search('columnName', array('value1', 'value2'))
```

To match a value in a subquery:

```php
$db->search('columnName', $db2);
```

To select a column:

```php
$db->select('columnName');
```

To select multiple columns:

```php
$db->select('column1Name');
$db->select('column2Name');
```
or
```php
$db->select(array('column1Name', 'column2Name'));
```

To sort by a value:

```php
$db->sort('columnName');
```

To sort by multiple values:

```php
$db->sort('column1Name');
$db->sort('column2Name');
```
or
```php
$db->sort(array('column1Name', 'column2Name');
```

To group by a value:

```php
$db->group('columnName');
```

To group by multiple values:

```php
$db->group('column1Name');
$db->group('column2Name');
```
or
```php
$db->group(array('column1Name', 'column2Name');
```

From, search, select, group, and sort can be chained for condensed programming:

```php
$db = new Db('connectionNameOrString');
$db->from('tableName')->select('column1Name')->search('columnName', 'columnValue')->sort('columnName');
```

Table, buildsql, and toarray can be appended to a chain to return a result:

```php
$db2 = new Db($db);
$db2->from('table2Name')->search('columnName', $db)->table();
```

Call from, search, select, group, and sort without parameters to clear previously entered values:

```php
$db->search();
```

To update the currently selected records with new values:

```php
$db->update(array(
  'column1Name' => 'column1Value',
  'column2Name' => 'column2Value'
));
```

To insert a new value into the table:

```php
$db->insert(array(
  'column1Name' => 'column1Value',
  'column2Name' => 'column2Value'
));
```

To delete all currently selected records:

```php
$db->delete();
```

Warning: if you do not search() prior to calling delete() all records will be deleted from the table.
