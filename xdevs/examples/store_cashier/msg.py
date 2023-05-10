class NewClient:
    def __init__(self, client_id, t_entered):
        self.client_id = client_id
        self.t_entered = t_entered

    def __str__(self):
        return f'id::{self.client_id}; t_entered::{self.t_entered}'

class ClientToEmployee:
    def __init__(self, new_client, employee_id):
        self.client = new_client
        self.employee_id = employee_id

    def __str__(self):
        return f'Client::{self.client} to Employee::{self.employee_id}'

class LeavingClient:
    def __init__(self, client_id, t_entered, t_exited):
        self.client_id = client_id
        self.t_entered = t_entered
        self.t_exited = t_exited

    def __str__(self):
        return f'Client::{self.client_id}; t_entered::{self.t_entered}; t_exited::{self.t_exited}'