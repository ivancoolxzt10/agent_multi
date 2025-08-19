from llm import llm


class BaseAgent:
    def __init__(self, llm_instance=None):
        self.llm = llm_instance if llm_instance is not None else llm
    def set_llm(self, llm):
        self.llm = llm
    def get_llm(self):
        return self.llm
