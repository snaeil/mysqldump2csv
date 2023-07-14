"""Converts a mysqldump file into csv files.
Every table in the mysqldump file will be converted into a csv file.
"""

import re
import codecs
import ast
import os
import sys

# read sql file
with codecs.open("dump.sql", "r", encoding="utf-8", errors="ignore") as f:
    sql = f.read()

EXCLUDED_TABLES = [
    "SPRING_SESSION",
    "SPRING_SESSION_ATTRIBUTES",
    "dependency",
    "dimension",
    "affected_dependency_dimension",
    "predecessor_dependency_dimension",
    "representing_dependency_dimension",
    "authentication",
    "evaluator",
    "general_item",
    "promis_cat_item",
    "general_response_option",
    "promis_cat_response_option",
    "report_template",
    "stw",
    "survey",
    "survey_dimension",
]
table_architecture = {}


def split_tuple_list_string(s: str) -> list:
    """splits a string containing a list of tuples (the values are embedded in parentheses), split by delimiter, but ignores delimiters and parentheses in escaped strings
    Args:
        s (str): the string to split

    Returns:
        list[str]: the list of tuples

    >>> split_tuple_list_string("('first)',1),('second',2)")
    [('first)', 1), ('second', 2)]
    >>> split_tuple_list_string("('first)',1),('se),(cond',2)")
    [('first)', 1), ('se),(cond', 2)]
    """
    return list(ast.literal_eval(s))


def replace_NULL_with_special(s: str, special: str = "'##anullvalue##'") -> str:
    """replaces all occurences of NULL with None"""
    return s.replace("NULL", special)


def replace_special_with_NULL(s: str, special: str = "'##anullvalue##'") -> str:
    """replaces all occurences of NULL with None"""
    return s.replace(special, "NULL")


def get_values_string_from_statement(s: str):
    """returns the values string from an insert statement
    Args:
        s (str): the insert statement

    Returns:
        str: the values string

    >>> get_values_string_from_statement("INSERT INTO `person` VALUES ('1',2,3),('4',5,6);")
    "('1',2,3),('4',5,6)"
    """
    return re.sub("INSERT INTO `.*` VALUES ", "", s).replace(";", "")


def to_csv(tables):
    """
    create csv files for every table in the out directory
    the first line of the csv file is the column names
    the following lines are the data
    """
    for table_name, table in tables.items():
        if not table["ignored"]:
            with open(os.path.join("out", table_name + ".csv"), "w") as f:
                f.write(",".join(table["column_names"]) + "\n")
                for row in table["data"]:
                    f.write(replace_special_with_NULL(str(row)) + "\n")
            print("wrote table " + table_name)
        else:
            print("ignored table " + table_name)


def run(filename):
    """
    Iterate over lines until the next "CREATE" statement is found and remember table name and column names
    The result [{'table_name': 'authentication', 'column_names': ['id', 'confirmed', 'password']}] is saved in table_architecture
    coming from the following sql statement:
    CREATE TABLE `authentication` (
      `id` varchar(255) NOT NULL,
      `confirmed` tinyint(1) NOT NULL,
      `password` varchar(255) NOT NULL,
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    for line in sql.splitlines():
        if line.startswith("CREATE TABLE"):
            table_name = re.findall("`(.*)`", line)[0]
            table_architecture[table_name] = {"column_names": [], "ignored": False}
        elif line.startswith("  `"):
            column_name = re.findall("`(.*)`", line)[0]
            table_architecture[table_name]["column_names"].append(column_name)
        elif line.startswith(")"):
            table_architecture[table_name]["data"] = []
    for t in table_architecture:
        if t not in EXCLUDED_TABLES:
            for line in sql.splitlines():
                if line.startswith("INSERT INTO `" + t):
                    stripped = get_values_string_from_statement(line)
                    tl = split_tuple_list_string(replace_NULL_with_special(stripped))
                    table_architecture[t]["data"] = tl
        else:
            table_architecture[t]["ignored"] = True

    to_csv(table_architecture)


# uses the single argument as the path to the sql file
def cli():
    filename = sys.argv[1]
    # check if file exists
    if not os.path.isfile(filename):
        print("File does not exist.")
        exit()
    run(filename)


if __name__ == "__main__":
    cli()
