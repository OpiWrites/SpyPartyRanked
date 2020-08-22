import json
import os

class Config:
    __configs = {}
    __saved = {}

    def __init__(self, path, default_config=None, load_logging=False):
        self.path = path
        self.verbose = load_logging
        self.__default = default_config
        if path not in self.__configs:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        self.__configs[path] = json.load(f)
                        if self.verbose:
                            print(f"reading config: {self.__configs[self.path]}")
                except:
                    with open(path, "a") as f:
                        self.__configs[path] = default_config
                        json.dump(self.__configs[path], f)
                        if self.verbose:
                            print("error reading config, using default:", default_config)
                for key in default_config:  # Allows newer versions of configs to add properties
                    if key not in self.__configs[path]:
                        if self.verbose:
                            print(f"+ added new property: '{key}': {default_config[key]}")
                        self.__configs[path][key] = default_config[key]
                # for key in self.configs[path]:
                #     if key not in default_config:
                #         if self.verbose:
                #             print(f"- removed property: '{key}': {self.configs[path][key]}")
                #         del self.configs[path][key]
            else:
                if self.verbose:
                    print("config not found, using default:", default_config)
                self.__configs[path] = default_config
        self.__saved[path] = True  # the config was just initialized, so there are no changes to be saved

    def save(self):
        if not self.__saved[self.path]:
            # built-in functions (such as open), do not work in __del__ for whatever reason, so
            # this must be called manually
            try:
                with open(self.path, "w") as f:
                    json.dump(self.__configs[self.path], f, indent=4)
                    if self.verbose:
                        print("writing config:", self.__configs[self.path])
            except:
                print("ERROR WHILE WRITING CONFIG???")

    def is_saved(self):
        return self.__saved[self.path]

    def __getitem__(self, item):
        return self.__configs[self.path][item]

    def __setitem__(self, key, value):
        if key in self.__default:
            self.__configs[self.path][key] = value
            self.__saved[self.path] = False

    def __delitem__(self, key):
        del self.__configs[self.path][key]
        self.__saved[self.path] = False

    def __str__(self):
        return str(self.__configs[self.path])

    def toggle(self, key):
        if key in self.__configs[self.path]:
            val = self.__configs[self.path][key]
            if type(val) == bool:
                val = not val
                self.__configs[self.path][key] = val
                self.__saved[self.path] = False
                return val

    def reset_to_defaults(self):
        self.__configs[self.path] = self.__default
        self.__saved[self.path] = False

