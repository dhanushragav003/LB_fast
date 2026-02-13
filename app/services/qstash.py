from qstash import QStash 
import json
from app.core.config import app_config

class schedule_task():
    def __init__(self):
        self.client=QStash(app_config.QSTASH_TOKEN)
    def create_schedule(self,payload,destination,cron,schedule_id=None):
        try:
            response=self.client.schedule.create(
                destination=destination,
                method="POST",
                cron=cron, 
                schedule_id = schedule_id,
                body=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                }
            )
            print("Schedule created!",response)
            return response
        except Exception as e:
            print(f"exception occured [{e}]")
            raise e
        
    def delete_schedule(self,job_id):
        try:
            response=self.client.schedule.delete(job_id)
            print("Schedule deleted!",response)
            #delete job id in db
        except Exception as e:
            print(f"exception occured [{e}]")

