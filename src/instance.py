import json

class Instance:
    def __init__(self, name):
        self.name = name
        with open(name, "r") as f:
            data = json.load(f)

        self.interpreters = data["Interpreters"]
        self.sessions = data["Sessions"]
        self.blocks = data["Blocks"]

        self.languages_per_interpreter = data["Languages_i"]
        self.languages_per_session = data["Languages_s"]
        self.sessions_per_block = data["Sessions_b"]

    def __str__(self):
        return (f"Instance: {self.name}\n"
                f"Interpreters: {self.interpreters}\n"
                f"Sessions: {self.sessions}\n"
                f"Blocks: {self.blocks}\n"
                f"Languages of interpreters: {self.languages_per_interpreter}\n"
                f"Languages per session: {self.languages_per_session}\n"
                f"Sessions per block: {self.sessions_per_block}")