<?php
    // Author: Cory Cook
    
    class Parameter
    {
        public $parameters = array();
        public $prefix;
        public $suffix;
        public $join;
    
        public function __construct($pre, $junc = ', ', $post = '') {
            $this->prefix = $pre;
            $this->join = $junc;
            $this->suffix = $post;
        }
    
        public function add($column, $argument = NULL) {
            if (is_null($argument)) {
                $this->parameters[] = $column;
            } else {
                $this->parameters[$column] = $argument;
            }
        }
    
        public function reset() {
            $this->parameters = array();
        }
    
        public function serialize() {
            if (count($this->parameters)) 
                return $this->prefix.implode($this->join, $this->parameters).$this->suffix;
            return NULL;
        }
    }
    
    class ValuesParameter extends Parameter
    {
        protected $stringset;

        public function __construct($prefix, $join = ', ', $suffix = '') {
            parent::__construct($prefix, $join, $suffix);
            $this->stringset = function(&$value, $key) {
                if (is_string($value)) $value = "'$value'";
            };
        }

        public function serialize() {
            if (count($this->parameters)) {
                $result_set = $this->parameters;
                array_walk($result_set, $this->stringset);
                return $this->prefix.implode($this->join, $result_set).$this->suffix;
            }
            return NULL;
        }
    }
    
    class SearchParameter extends ValuesParameter
    {
        protected $set;

        public function __construct() {
            parent::__construct(' WHERE ', ' AND ');
            $this->set = function(&$value, $key) {
                if (is_int($key)) {
                } else if (is_string($value)) {
                    $value = "$key LIKE '$value'";
                } else if (is_array($value)) {
                    array_walk($value, $this->stringset);
                    $value = "$key IN (".implode(', ', $value).")";
                } else if ($value instanceof DbEngine) {
                    $value = "[$key] IN (".$value->tosql().")";
                }
                else {
                    $value = "[$key]=$value";
                }
            };
        }
    
        public function serialize() {
            if (count($this->parameters)) {
                $result_set = $this->parameters;
                array_walk($result_set, $this->set);
                return $this->prefix.implode($this->join, $result_set);
            }
            return NULL;
        }
    }
    
    class SetParameter extends ValuesParameter
    {
        protected $set;
    
        public function __construct() {
            parent::__construct(' SET ', ', ');
            $this->set = function(&$value, $key) {
                $value = "[$key]=$value";
            };
        }
    
        public function serialize() {
            if (count($this->parameters)) {
                $result_set = $this->parameters;
                array_walk($result_set, $this->stringset);
                array_walk($result_set, $this->set);
                return $this->prefix.implode($this->join, $result_set).$this->suffix;
            }
            return NULL;
        }
    }
    
    class SelectParameter extends Parameter
    {
        public function __construct() {
            parent::__construct('SELECT ');
        }
    
        public function serialize() {
            if (count($this->parameters)) {
                return parent::serialize();
            }
            return $this->prefix.'*';
        }
    }
    
    class DbEngine
    {
        protected $connection;
        protected $parameters = array();
        protected $state, $checkstate, $res;
        protected $tablename;
    
        public function __construct($db, $username = NULL, $password = NULL) {
            $this->parameters['search'] = new SearchParameter();
            if ($db instanceof DbEngine) {
                $this->connection = $db->connection;
                if (!is_null($db->tablename)) $this->from($db->tablename);
                $this->parameters['search']->parameters = $db->parameters['search']->parameters;
            } else {
                $this->connection = odbc_connect($db, $username, $password) or 
                die('Database Connection Failed');
            }
            $this->refresh();
        }
    
        public function __destruct() {
            if (is_resource($this->connection)) {
                odbc_close($this->connection);
            }
        }
    
        public function tosql() {
            $sql = '';
            foreach ($this->parameters as $param) {
                $sql .= $param->serialize();
            }
            return $sql;
        }
    
        protected function parameter($param, $col = NULL, $arg = NULL) {
            if (is_array($col)) {
                if (!is_array($arg)) $arg = array($arg);
                foreach($col as $i => $column) {
                    $this->parameters[$param]->add($column, array_key_exists($i, $arg) ? $arg[$i] : NULL);
                }
            } else if (is_null($col)) {
                $this->parameters[$param]->reset();
            }
            else {
                $this->parameters[$param]->add($col, $arg);
            }
            $this->refresh();
        }
    
        public function from($t = NULL, $alias = NULL) {
            $this->tablename = $t;
            $this->parameter('from', $t, $alias);
            return $this;
        }
    
        public function search($col = NULL, $arg = NULL) {
            $this->parameter('search', $col, $arg);
            return $this;
        }
    
        public function toarray() {
            $result = array();
            while ($arr = odbc_fetch_array($this->result())) {
                $result[] = $arr;
            }
            $this->refresh();
            return $result;
        }
    
        public function result() {
            if ($this->state == $this->checkstate) return $this->res;
            $this->res = odbc_exec($this->connection, $this->tosql());
            $this->checkstate = $this->state;
            return $this->res;
        }
    
        public function tables() {
            $result = odbc_tables($this->connection);
            $result_set = array();
            while(odbc_fetch_row($result)) {
                if (odbc_result($result, "TABLE_TYPE")=="TABLE")
                    $result_set[] = odbc_result($result, "TABLE_NAME");
            }
            return $result_set;
        }
    
    
        public function count() {
            $db = new Db($this);
            $db->select('COUNT(*) as val');
            return odbc_fetch_array($db->result())['val'];
        }
    
        public function columns() {
            $result = array();
            $set = odbc_columns($this->connection);
            while ($arr = odbc_fetch_array($set)) {
                if (in_array($arr['TABLE_NAME'], $this->parameters['from']->parameters))
                    $result[] = $arr;
            }
            return $result;
        }
    
        protected function refresh() {
            $this->state = rand();
            if (is_resource($this->res)) {
                odbc_free_result($this->res);
            }
        }
    
        public function reset() {
            foreach($this->parameters as $parameter) {
                $parameter->reset();
                $this->from($tablename);
            }
        }
    }
    
    class SelectEngine extends DbEngine
    {
        public function __construct($db, $username = NULL, $password = NULL) {
            $this->parameters['select'] = new SelectParameter();
            $this->parameters['from'] = new Parameter(' FROM ');
            parent::__construct($db, $username, $password);
            $this->parameters['group'] = new Parameter(' GROUP BY ');
            $this->parameters['sort'] = new Parameter(' ORDER BY ');
        }
    
        public function group($col = NULL) {
            $this->parameter('group', $col);
            return $this;
        }
    
        public function sort($col = NULL) {
            $this->parameter('sort', $col);
            return $this;
        }
    
        public function select($col = NULL, $alias = NULL, $raw = FALSE) {
            $this->parameter('select', $col);
            return $this;
        }
    
        public function result($col = NULL) {
            if (!is_null($col)) {
                $this->select();
                $this->select($col);
            }
            return parent::result();
        }
    
        public function tohtml($col = NULL) {
            if (!$this->count()) echo '<p>No data</p>';
            else odbc_result_all($this->result($col));
            $this->refresh();
        }
    }
    
    class InsertEngine extends DbEngine
    {
        public function __construct($db, $username = NULL, $password = NULL) {
            $this->parameters['from'] = new Parameter('INSERT INTO ');
            $this->parameters['keys'] = new Parameter(' (', ', ', ')');
            $this->parameters['values'] = new ValuesParameter(' VALUES (', ', ', ')');
            parent::__construct($db, $username, $password);
            $this->parameters['search']->reset();
        }
    
        public function insert($arr) {
            foreach ($arr as $key => $value) {
                $this->parameter('keys', $key);
                $this->parameter('values', $value);
            }
            return $this->result();
        }
    }
    
    class UpdateEngine extends DbEngine
    {
        public function __construct($db, $username = NULL, $password = NULL) {
            $this->parameters['from'] = new Parameter('UPDATE ');
            $this->parameters['set'] = new SetParameter();
            parent::__construct($db, $username, $password);
        }
    
        public function update($arr) {
            foreach ($arr as $key => $value) {
                $this->parameter('set', $key, $value);
            }
            return $this->result();
        }
    
        public function set($col = NULL, $arg = NULL) {
            $this->parameter('set', $col, $arg);
            return $this;
        }
    }
    
    class DeleteEngine extends DbEngine
    {
        public function __construct($db, $username = NULL, $password = NULL) {
            $this->parameters['from'] = new Parameter('DELETE FROM ');
            parent::__construct($db, $username, $password);
        }
    
        public function delete() {
            return $this->result();
        }
    }
    
    class Db extends SelectEngine
    {
        public function __construct($db, $username = NULL, $password = NULL) {
            parent::__construct($db, $username, $password);
        }
    
        public function insert($arr) {
            $Eng = new InsertEngine($this);
            $Eng->insert($arr);
        }
    
        public function update($arr) {
            $Eng = new UpdateEngine($this);
            $Eng->update($arr);
        }
    
        public function delete() {
            $Eng = new DeleteEngine($this);
            $Eng->delete();
        }
    }
    
?>
