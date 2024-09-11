import inspect
import functools
import importlib
import os
import sys
from typing import KeysView, Optional, Union

from bot import ModerationBot
from events.base import EventHandler

class EventRegistry:
    """Event registry class that handles dynamic class loading and getting info for an event handler"""

    def __init__(self) -> None:
        self.event_handlers = {}
        self.py_files = []
        self.new_py_files = []
        self.modules = []
        self.module_changes = False
        print(
            "Initializing the event registry handler. This does not start registering events!"
        )
        self.get_py_files(overwrite=True)

    def set_instance(self, instance: ModerationBot) -> None:
        """Gives the event registry and instance of the bot"""
        self.instance = instance

    def register(self, event: str, instance: ModerationBot) -> None:
        """Method that registers event modules"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        if instance not in self.event_handlers[event]:
            self.event_handlers[event].append(instance)
        else:
            print("Event Instance already present: " + instance)

    def unregister(self, event: str, instance: ModerationBot) -> None:
        """Method to unregister an event module by name"""
        try:
            self.event_handlers[event].remove(instance)
            if len(self.event_handlers[event]) == 0:
                self.event_handlers.pop(event)
                delattr(self.instance, event)
        except KeyError:
            pass

    def get_py_files(self, overwrite: Optional[bool] = False) -> None:
        """Gets a list of python files in the events directory"""
        from bot import __location__

        new_py_files = [
            py_file
            for py_file in os.listdir(os.path.join(__location__, "events"))
            if os.path.splitext(py_file)[1] == ".py"
        ]
        if len(new_py_files) != self.py_files:
            self.new_py_files = new_py_files
            self.module_changes = True
            if overwrite:
                self.py_files = new_py_files

    def register_events(self) -> None:
        """Registers all events with the bot"""
        print("Registering events...")
        self.event_handlers.clear()
        self.modules = [str(m) for m in sys.modules if m.startswith("events.")]
        for module in self.modules:
            if "base" not in module:
                del sys.modules[module]

        for event_file in self.py_files:
            fname = os.path.splitext(event_file)[0]
            if fname == "base":
                continue
            event_module = importlib.import_module(f"events.{fname}")

            # Use inspect to get all classes in the module
            classes = inspect.getmembers(event_module, inspect.isclass)

            for name, class_ref in classes:
                # Check if the event handler class is a subclass of the base event handler
                if issubclass(class_ref, EventHandler) and class_ref is not EventHandler:
                    clazz = class_ref(self.instance)
                    clazz.register_self()
                    event_name = clazz.event
                    if event_name is not None:
                        if not hasattr(self.instance, event_name):
                            setattr(
                                self.instance,
                                event_name,
                                functools.partial(
                                    self.instance.event_template, event_name=event_name
                                ),
                            )
                    else:
                        print(f"Event handler has no event name: {name}")
                        clazz.unregister_self()

    async def reload_events(self) -> None:
        self.get_py_files()
        if self.module_changes:
            self.module_changes = False
            self.py_files = self.new_py_files
            self.register_events()

    def get_all_event_handlers(self) -> KeysView[str]:
        return self.event_handlers.keys()

    def get_event_handlers(self, event) -> Union[list, None]:
        try:
            return self.event_handlers[event]
        except KeyError:
            print("No event handlers registered for event.")
            return None


event_registry = EventRegistry()
