"""Non-secret same-user trigger for the existing private desktop singleton."""
import threading,time,uuid
from pathlib import Path
from sources import write_json
from wechat_review import read_json

def request_run(base,discover_only=False):
    root=Path(base)/'automation';root.mkdir(parents=True,exist_ok=True)
    value={'id':uuid.uuid4().hex,'created_at':time.time(),'discover_only':bool(discover_only)}
    write_json(root/'trigger.json',value)
    return {'queued':True,'trigger_id':value['id']}

def consume(studio):
    path=studio.autofeed.root/'trigger.json'
    if not path.exists():return
    value=read_json(path,{})
    path.unlink(missing_ok=True)
    if time.time()-value.get('created_at',0)>600:return
    try:
        studio.autofeed.start(discover_only=value.get('discover_only') is True)
    except ValueError as exc:studio.autofeed.message(str(exc))

def listen(studio):
    def loop():
        while not studio.closing:
            try:consume(studio)
            except (OSError,ValueError):pass
            time.sleep(2)
    thread=threading.Thread(target=loop,name='autofeed-trigger',daemon=True);thread.start()
    return thread
