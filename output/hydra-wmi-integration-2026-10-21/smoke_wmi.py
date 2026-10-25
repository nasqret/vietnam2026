import json,sys,threading
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'hydra-playground'))
import server
request={"theorem":"0 = 0","search_mode":"sequential","search_profile":"sequential","model_id":"wmi-c6-vanilla47","max_model_calls":32,"beam_width":1}
def progress(event): print(json.dumps({"progress":event}),flush=True)
result=server.run_worker("search",request,threading.Event(),progress)
(root/'output/hydra-wmi-integration-2026-10-21/SMOKE_WMI.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
r=result.get("result") or {}
print(json.dumps({"error":result.get("error"),"exit":result.get("worker_exit_code"),"status":r.get("status"),"search":r.get("search"),"commands":r.get("commands")}),flush=True)
