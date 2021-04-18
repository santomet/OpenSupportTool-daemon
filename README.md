# Open Support Tool - Agent

Agent for the Open Support Tool - Linux version
Please let the deployment of the agent on the API: It will use the releases available here "compiled" into the bytecode.

To make it work the data.json file must have this structure:
```
{
  "token": "83f6ef295a6b38be3b5eef224e7cec23d0446dc426d864719ec362535524c077f591c64cdfe85401080882f152",
  "server_protocol": "https://",
  "server_domain_ip": "0.0.0.0",
  "server_port": 8000,
  "interval_seconds": 5,
  "tunnels": []
}
```

Please never use HTTP protocol for anything other than testing - correctly deployed API should not allow that!