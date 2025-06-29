#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import re
import argparse
import xml.etree.ElementTree as ET

def create_set_method_name(attr_name):
    """Create set method name from attribute name"""
    return f"set{snake_to_camel(attr_name).capitalize()}"

def create_get_method_name(attr_name):
    """Create get method name from attribute name"""
    return f"get{snake_to_camel(attr_name).capitalize()}"

def create_property_name(attr_name):
    """Create property name from attribute name"""
    return f"_{attr_name}"

def snake_to_camel(snake_str):
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])

def generate_interface_constants(attributes):
    """Generate interface constants for attributes"""
    constants = []
    for attr_name, attr_type in attributes:
        constant_name = attr_name.upper()
        constants.append(f"    public const {constant_name} = '{attr_name}';")
    return "\n".join(constants)

def generate_interface_methods(attributes):
    """Generate interface methods for attributes with single blank line separation"""
    methods = []
    for i, (attr_name, attr_type) in enumerate(attributes):
        camel_attr_name = snake_to_camel(attr_name)
        method_suffix = camel_attr_name[0].upper() + camel_attr_name[1:]

        # setter
        methods.append(
            f"    /**\n"
            f"     * Setter for {attr_name}\n"
            f"     *\n"
            f"     * @param {attr_type} ${camel_attr_name}\n"
            f"     * @return $this\n"
            f"     */\n"
            f"    public function set{method_suffix}({attr_type} ${camel_attr_name}): self;"
        )

        # getter
        methods.append(
            f"\n"
            f"    /**\n"
            f"     * Getter for {attr_name}\n"
            f"     *\n"
            f"     * @return {attr_type}|null\n"
            f"     */\n"
            f"    public function get{method_suffix}(): {attr_type};" + ("\n" if i != len(attributes) - 1 else "")
        )
    return "\n".join(methods)

def generate_data_class_methods(attributes):
    """Generate data class methods for attributes with single blank line separation"""
    methods = []
    for i, (attr_name, attr_type) in enumerate(attributes):
        camel_attr_name = snake_to_camel(attr_name)
        method_suffix = camel_attr_name[0].upper() + camel_attr_name[1:]
        const = attr_name.upper()

        # Setter
        methods.append(
            f"    /**\n"
            f"     * Setter for {attr_name}\n"
            f"     *\n"
            f"     * @param {attr_type} ${camel_attr_name}\n"
            f"     * @return $this\n"
            f"     */\n"
            f"    public function set{method_suffix}({attr_type} ${camel_attr_name}): self\n    {{\n"
            f"        return $this->setData(self::{const}, ${camel_attr_name});\n"
            f"    }}"
        )

        # Getter
        methods.append(
            f"\n"
            f"    /**\n"
            f"     * Getter for {attr_name}\n"
            f"     *\n"
            f"     * @return {attr_type}|null\n"
            f"     */\n"
            f"    public function get{method_suffix}(): {attr_type}\n    {{\n"
            f"        return $this->getData(self::{const});\n"
            f"    }}" + ("\n" if i != len(attributes) - 1 else "")
        )

    return "\n".join(methods)

TEMPLATE_DATA_INTERFACE = """<?php
declare(strict_types=1);

namespace {vendor}\\{module}\\Api\\Data;

/**
 * {entity} data interface
 *
 * @api
 */
interface {entity}Interface
{{
{interface_constants}

{interface_methods}
}}
"""

TEMPLATE_DATA_CLASS = """<?php
declare(strict_types=1);

namespace {vendor}\\{module}\\Model\\Data;

use Magento\\Framework\\Model\\AbstractExtensibleModel;
use {vendor}\\{module}\\Api\\Data\\{entity}Interface;

/**
 * {entity} data model
 *
 * @api
 */
class {entity} extends AbstractExtensibleModel implements {entity}Interface
{{
{data_methods}
}}
"""

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"Generated: {path}")

def parse_attributes(attributes_str):
    """Parse attributes string in format: name:type,name2:type2"""
    if not attributes_str:
        return []

    attributes = []
    for attr in attributes_str.split(','):
        if ':' in attr:
            name, attr_type = attr.strip().split(':', 1)
            attributes.append((name.strip(), attr_type.strip()))
        else:
            attributes.append((attr.strip(), 'string'))

    return attributes

def generate_data_object(vendor: str, module: str, entity: str, attributes: list):
    base_path = Path(f"app/code/{vendor}/{module}")
    interface_path = base_path / f"Api/Data/{entity}Interface.php"
    data_path = base_path / f"Model/Data/{entity}.php"

    interface_constants = generate_interface_constants(attributes)
    interface_methods = generate_interface_methods(attributes)
    data_methods = generate_data_class_methods(attributes)

    ctx = {
        "vendor": vendor, 
        "module": module, 
        "entity": entity,
        "interface_constants": interface_constants,
        "interface_methods": interface_methods,
        "data_methods": data_methods
    }

    write_file(interface_path, TEMPLATE_DATA_INTERFACE.format(**ctx))
    write_file(data_path, TEMPLATE_DATA_CLASS.format(**ctx))

def parse_magento_schema(schema_path):
    tree = ET.parse(schema_path)
    root = tree.getroot()

    # Define xsi namespace mapping
    ns = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    tables = []

    for table in root.findall("table"):
        table_name = table.get("name")
        columns = []

        for column in table.findall("column"):
            column_name = column.get("name")
            # Get the xsi:type attribute using namespace
            column_type = column.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}type')

            columns.append({
                "name": column_name,
                "type": column_type
            })

        tables.append({
            "table": table_name,
            "columns": columns
        })

    return tables

def map_db_type_to_php_type(db_type):
    """Map Magento DB types to PHP types"""
    mapping = {
        "int": "int",
        "smallint": "int",
        "bigint": "int",
        "decimal": "float",
        "float": "float",
        "double": "float",
        "boolean": "bool",
        "varchar": "string",
        "text": "string",
        "timestamp": "\\DateTimeInterface",
        "datetime": "\\DateTimeInterface",
        "date": "\\DateTimeInterface"
    }
    return mapping.get(db_type.lower(), "string")

def convert_table_to_entity(table_name):
    """Convert table name (e.g. bss_custom_entity) to PascalCase entity name (e.g. CustomEntity)"""
    parts = table_name.split('_')
    relevant = parts[-2:] if len(parts) > 1 else parts
    return ''.join(word.capitalize() for word in relevant)

def main():
    parser = argparse.ArgumentParser(description='Generate Magento 2 Data Object classes based on DB schema.')
    parser.add_argument('-v', '--vendor', required=True, help='Vendor name', metavar='')
    parser.add_argument('-m', '--module', required=True, help='Module name', metavar='')
    parser.add_argument('-e', '--entity', required=False, help='Entity name, if there no entity name, it will be generated from table name', metavar='')
    parser.add_argument('-db', '--db_schema', required=True, help='Path to db_schema.xml file', metavar='')

    args = parser.parse_args()

    vendor = args.vendor.strip()
    module = args.module.strip()
    db_schema_path = args.db_schema.strip()

    if not os.path.exists(db_schema_path):
        print(f"Error: File not found: {db_schema_path}")
        sys.exit(1)

    tables = parse_magento_schema(db_schema_path)
    if not tables:
        print("No tables found in schema.")
        sys.exit(1)

    print("Available tables:")
    for i, t in enumerate(tables):
        print(f"  [{i + 1}] {t['table']}")

    index = 0
    if len(tables) > 1:
        index = input(f"Select a table [1-{len(tables)}]: ").strip()
        if not index.isdigit() or not (1 <= int(index) <= len(tables)):
            print("Invalid selection.")
            sys.exit(1)
        index = int(index) - 1

    table = tables[index]
    if not args.entity:
        entity = convert_table_to_entity(table["table"])
    else:
        entity = args.entity

    attributes = [
        (col["name"], map_db_type_to_php_type(col["type"]))
        for col in table["columns"]
    ]

    generate_data_object(vendor, module, entity, attributes)

if __name__ == "__main__":
    main()
