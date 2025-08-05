# Malicious IP Restriction Workflow

## Alert Analysis

Sample alert: "`<malicious-ip>` is performing SSH brute force attacks against `<instance-id>`. Brute force attacks are used to gain unauthorized access to your instance by guessing the SSH password."

## Step 1: Check Malicious Status

Run this to get the malicious status:

```bash
curl --request GET \
--url https://www.virustotal.com/api/v3/ip_addresses/<malicious-ip> \
--header 'accept: application/json' \
--header 'x-apikey: <virustotal-api-key>'
```

**Path Params:** ip: `<malicious-ip>`

## Step 2: If Malicious - Update KubeArmor Policies

1. Find the relevant policy from existing KubeArmor policies and update it accordingly:

   - Repository: https://github.com/kubearmor/policy-templates/
   - Look for SSH-related policies
   - Update the policy to block the malicious IP

2. Apply the updated policy:
   ```bash
   kubectl apply -f policy.yaml
   ```
   **Note:** This command needs to be run on the specific cluster `<instance-id>`

## Step 3: Infrastructure-Specific Actions

### For AWS Instances:

- Go to Security Group (via terminal) and apply the policy
- Block the malicious IP at the security group level

### For SSH Linode:

- Go to Host and apply the policy
- Block the malicious IP at the host level

## Instructions:

1. **Analyze the alert** and extract the malicious IP and instance ID
2. **Check VirusTotal** for the IP's malicious status
3. **If confirmed malicious:**
   - Find appropriate KubeArmor policy from the templates repository
   - Update the policy to include the malicious IP
   - Apply the policy to the affected cluster
   - Take infrastructure-specific blocking actions (AWS Security Group or Linode Host)
4. **Provide recommendations** for:
   - Additional security measures
   - Monitoring improvements
   - Prevention strategies

## Placeholder Values:

- `<malicious-ip>`: Replace with actual malicious IP address
- `<instance-id>`: Replace with actual instance ID
- `<virustotal-api-key>`: Replace with actual VirusTotal API key
