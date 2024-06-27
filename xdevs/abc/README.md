# What is a Factory

A factory is a software methodology for designing and implementing objects that have a common behavior but several possible implementations. This type of methodology is widely used in this repository for creating different components in the simulations such as transducers, handlers, models, etc.

## Example 1 
_(Focused on handlers, transducer and celldevs)_

1. Firstly, a father abstract class is defined, which states the common behavior of the component under developing. (The class `InputHandler` may be found in `xdevs.abc.handler`)
2. A child class that inherits the behavior of its father defines the particular implementation. (The folder `xdevs.plugins.input_handlers.` stores several implementations for this class)
3. An entry point is defined. This name will play the role of a key that links the name to the desired implementation. (In the script `xdevs.pyproject`, the keys for Input Handlers are found after the `[project.entry-points."xdevs.input_handlers"]` statement)
4. Creating an instance of each implementation is as easy as passing to a method of the factory class the desired key and the required parameters (if any) for that specific implementation (Using the class `InputHandlers` in `xdevs.factory` and calling the method `create_input_handler`).

## Example 2 

_(Focused on `JSON` to `DEVS` components)_

In case of the `JSON` to `DEVS` model conversion, the factory methodology is used to create the components defined in the `JSON` file. The `Factory` class is in charge of creating the different types of implementations of an abstract class based on a key that is linked to the desired implementation.

1. The `DEVS` model must be defined (i.e. `EFP` in `xdevs.examples.gpt.models`).
2. The entry point must be created in pyproject.toml after `[project.entry-points."xdevs.components"]`

With this methodology, adding several instances of a component for a range of simulations is easier.
Defining a key that links to the desired implementation allows for a more straightforward way to create the components
and avoids having to create and define each component for each simulation.