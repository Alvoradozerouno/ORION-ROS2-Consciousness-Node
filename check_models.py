import urllib.request, json
r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
models = [m['name'] for m in json.loads(r.read()).get('models',[])]
key = ['qwen2.5:1.5b','orion-genesis:latest','orion-v3:latest','orion-sik:latest','phi3:mini']
print('Wichtige Modelle:')
for m in key:
    status = 'OK' if m in models else 'FEHLT'
    print(f'  {status} - {m}')
print(f'Gesamt: {len(models)} Modelle')
for m in models[:12]:
    print(f'  -> {m}')
