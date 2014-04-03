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
$db = new Db('connectionNameOrString');
```

Select a table to perform actions on:
```php
$db->from('tableName');
```

To display the table 'tableName' in HTML:

```php
$db->from('tableName');
$db->table();
```

To retrieve generated SQL command:

```php
$db->buildsql();
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

To copy connection and table information:

