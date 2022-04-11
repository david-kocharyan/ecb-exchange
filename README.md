<div id="top"></div>
<h1 align="center">Rivery Mini Test - Home Assignment</h1>
<h2 align="center">Currency Exchange Rate</h2>

## About The Project

Build a ​ Python​ process that gets data from the European Central Banks’ currency rates exchange service, at the next
address:
https://sdw-wsrest.ecb.europa.eu/help/

### Installation

Here's instruction for running script._

1. Move to the working directory, install and activate your virtualenv`
   ```shell
    cd /project_path 
   ```
   ```shell
    python -m venv yourVenvName
   ```
   ```shell
    source yourVenvName/bin/activate
   ```

2. Install requirements`
   ```shell
    pip install -r requirements.txt
   ```

3. Run script`
   ```shell
    python ecb.py
   ```

### Other information
<ul>
   <li>from_currencies - list</li>
   <li>to_currencies - list</li>
   <li>from_date - date</li>
   <li>to_date - date</li>
   <li>with_euro - boolean</li>
   <li>format - string, ( 'json' or 'csv' )</li>
</ul>

<p align="center"><a href="#top">Back to top</a></p>