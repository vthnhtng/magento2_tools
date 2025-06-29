# Data Object Generator

Generates Magento 2 Data Object classes (interfaces and models) from `db_schema.xml` files.

## Purpose

Automatically creates PHP Data Object classes following Magento 2 standards by parsing database schema definitions. Generates both interface and implementation classes with proper getter/setter methods.

## Usage

```bash
python generate_data_object.py -v <vendor> -m <module> -db <path_to_db_schema.xml>
```

### Parameters

- `-v, --vendor`: Vendor name (required)
- `-m, --module`: Module name (required)  
- `-e, --entity`: Entity name (optional)
- `-db, --db_schema`: Path to db_schema.xml file (required)

### Example

```bash
python generate_data_object.py -v MyVendor -m MyModule -db app/code/MyVendor/MyModule/etc/db_schema.xml
```

## Output

Creates two files:
- `app/code/{Vendor}/{Module}/Api/Data/{Entity}Interface.php`
- `app/code/{Vendor}/{Module}/Model/Data/{Entity}.php`

## Requirements

- Python 3.6+
- Magento 2 db_schema.xml file

## Installation

1. Ensure you have Python 3.6 or higher installed
2. The tool is a standalone Python script - no additional dependencies required

### Clone Only the Script

To clone only the `generate_data_object.py` file from the repository:

```bash
# Clone script
git clone https://github.com/vthnhtng/magento2_tools.git temp-clone
cp ./temp-clone/data_object_generator/generate_data_object.py ./
rm -rf temp-clone
```

## Type Mapping

The tool automatically maps database types to PHP types:

| Database Type | PHP Type |
|---------------|----------|
| int, smallint, bigint | int |
| decimal, float, double | float |
| boolean | bool |
| varchar, text | string |
| timestamp, datetime, date | \DateTimeInterface |
