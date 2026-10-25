import json,os
from pathlib import Path
root=Path('/net/slurm/releases');names=list(root.iterdir());assert len(names)<=128
result={'uid':os.getuid(),'read_only':True,'clients':[]}
for path in sorted(names):
 if path.name.startswith('production.'):
  client=path/'bin/scontrol'
  result['clients'].append({'directory':str(path),'client':str(client),'exists':client.is_file(),'resolved':str(client.resolve())})
print(json.dumps(result))
