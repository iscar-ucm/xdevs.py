# JSON to `xDEVS` Simulations

The `json` folder contains two examples of how to generate a `DEVS` model using a `JSON` file, these examples are the `efp.json` and `gpt.json`.

Next, a concise guide on using the `from_json` method from `xdevs.factory` to parse a `JSON` file into a `DEVS` model is presented. 
For detailed information, please refer to the method's documentation.

## Overview

The `from_json` method allows you to parse a `JSON` file into a `DEVS` model. The `JSON` file must follow specific rules to correctly define components and their couplings.

**ATTENTION PLEASE**  ❗❗

 Take into account that the `component_id` inside the `JSON` file must be identified as an `entry-point` of `Components`  in `xdevs.factory `. (See the `Factory` section in `xdevs.abc` for more information).


## JSON Structure

### Master Component

The top-level JSON object represents the master component.

```json
{
    "MasterComponentName": {
        "components": {
            // Nested components
        },
        "couplings": [
            // List of couplings
        ]
    }
}
```

### Components

Components can be either already registered in the `entry-points` or couple:

* Coupled: Contains `components` and `couplings` keys. 
* Component: Identified by the `component_id` key. It must be already defined in the `entry-points`.


```json
"components": {
    "CoupledModel1": {
        "components": {
            // Nested components
        },
        "couplings": [
            // List of connection dictionaries
        ]
    },
    "Component2": {
        "component_id": "ID_from_factory",
        "args": [/* positional arguments */],
        "kwargs": {
            "a_parameter": "value",
            // Other keyword arguments
        }
    }
    // Additional components
}

```

### Couplings
Couplings define connections between components:

* IC (Internal Coupling): Both componentFrom and componentTo are specified.
* EIC (External Input Coupling): componentFrom is missing. (A new input port is created)
* EOC (External Output Coupling): componentTo is missing. (A new output port is created)

```json
"couplings": [
    {
        "componentFrom": "Model1",
        "portFrom": "PortA", // Port name defined in Model1
        "componentTo": "Model2",
        "portTo": "PortB"
    }
    // Additional couplings
]
```  

## Example

```bash
$ cd xdevs/examples/json
$ python3 json2xdevs_example.py
```
