class Base_agent:
    def __init__(self, name):
        self.name = name
 
    def get_move(self, board, time_left=None, increment=0.0):
        raise NotImplementedError