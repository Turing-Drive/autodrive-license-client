# AutoDrive License Client Tools

This repository provides helper scripts for generating license requests for **AutoDrive**.  
It collects a set of hardware identifiers (HWID) from the target machine, hashes them,  
and writes out a JSON file that can be sent to AutoDrive for license activation.  

## Features
- Collects hardware identifiers without using MAC addresses  
- Generates reproducible HWID (SHA-256) from system components  
- Produces a `license_request.json` file ready to send to AutoDrive  
- Simple command-line usage (Python 3.x required)  

## Installation
Clone the repository to the target machine where you want to generate the license request:

```bash
git clone https://github.com/Turing-Drive/autodrive-license-client.git
cd autodrive-license-client
```

Ensure Python 3 is available:

```bash
python3 --version
```

No additional dependencies are required (only Python standard library).

### Get HWID from target machine

```bash
python3 ./collect_tools/collect_hwid.py --customer <YOUR_COMPANY_NAME>
```

This will generate a file license_request.json in the current directory.
It also prints the HWID SHA-256 hash to the console.

## Output Format

The generated JSON file contains:

```json
{
  "version": 1,
  "timestamp": 1712345678,
  "customer": "YourCompany",
  "features": ["AutoDrive"],
  "hwid_components": [
    "brd:1234567890",
    "dmi:abcd-ef01-2345-6789",
    "fs:1111-2222",
    "mid:deadbeefcafebabe"
  ],
  "hwid_sha256": "6b08a0f3...",
  "env": {
    "uname": "Linux 5.15.0-72-generic",
    "in_docker_hint": false
  }
}
```

## Next Step

Please send the generated `license_request.json` file  
to your AutoDrive business contact for license activation.

After AutoDrive provides you with the `license.json` file,  
you just need to run the provided script `autodrive-license-install.sh` on the target machine.  

### Usage

1. Place `license.json` and `autodrive-license-install.sh` in the same directory.  
2. Run the script:

```bash
chmod +x autodrive-license-install.sh
./autodrive-license-install.sh
```

## License

Licensed under the Apache License 2.0.
