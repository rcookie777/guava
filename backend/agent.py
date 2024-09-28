
class AgentTask:
    def __init__(self, task, status):
        self.task = task
        self.status = status

    def to_dict(self):
        return {
            'task': self.task,
            'status': self.status
        }

